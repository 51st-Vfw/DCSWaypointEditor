'''

main_gui.py: GUI for DCS Waypoint Editor main window

'''

import base64
import keyboard
import os
import pyperclip
import pytesseract
import PySimpleGUI as PyGUI
import queue
import src.pymgrs as mgrs
import tkinter as tk
import winsound
import zlib

from LatLon23 import LatLon, Longitude, Latitude
from peewee import DoesNotExist
from slpp import slpp as lua

from src.cf_xml import CombatFliteXML
from src.comp_dcs_bios import dcs_bios_is_current, dcs_bios_vers_install, dcs_bios_vers_latest, dcs_bios_install
from src.comp_dcs_we import dcs_we_is_current, dcs_we_vers_install, dcs_we_vers_latest, dcs_we_install
from src.dcs_f10_capture import dcs_f10_capture_map_coords, dcs_f10_parse_map_coords_string
from src.gui_util import gui_update_request, gui_backgrounded_operation, gui_verify_dcs_running
from src.gui_util import gui_text_strike, gui_text_unstrike
from src.gui_util import airframe_list, airframe_type_to_ui_text, airframe_ui_text_to_type
from src.logger import get_logger
from src.mission_package import dcswe_install_mpack
from src.objects import Profile, Waypoint, MSN
from src.prefs_gui import DCSWEPreferencesGUI

UX_SND_ERROR = "data/ux_error.wav"
UX_SND_INJECT_TO_JET = "data/ux_action.wav"
UX_SND_F10CAP_TOGGLE_MODE = "data/ux_action.wav"
UX_SND_F10CAP_GOT_WAYPT = "data/ux_cap_wypt.wav"
UX_SND_F10CAP_GOT_PANEL = "data/ux_cap_cpan.wav"

def json_zip(j):
    j = base64.b64encode(
        zlib.compress(
            j.encode('utf-8')
        )
    ).decode('ascii')
    return j

def json_unzip(j):
    return zlib.decompress(base64.b64decode(j)).decode('utf-8')

class DCSWEMainGUI:
    def __init__(self, editor, dcs_we_version, dcs_bios_version):
        self.editor = editor
        self.dcs_we_version = dcs_we_version
        self.dcs_bios_version = dcs_bios_version

        self.logger = get_logger(__name__)
        self.hkey_pend_q = queue.Queue()
        self.menu_pend_q = queue.Queue()
        self.profile = None
        self.scaled_dcs_gui = False
        self.is_dcs_f10_enabled = False
        self.is_dcs_f10_tgt_add = False
        self.is_profile_dirty = False
        self.is_waypoint_dirty = False
        self.tk_menu_dcswe = None
        self.tk_menu_profile = None
        self.tk_menu_mission = None
        self.values = None
        self.selected_wp_type = "WP"

        self.load_profile()

        try:
            with open(f"{self.editor.prefs.path_dcs}\\Config\\options.lua", "r") as f:
                dcs_settings = lua.decode(f.read().replace("options = ", ""))
                self.scaled_dcs_gui = dcs_settings["graphics"]["scaleGui"]
            self.logger.info(f"DCS GUI scale is: {self.scaled_dcs_gui}")
        except (FileNotFoundError, ValueError, TypeError):
            self.logger.error("Failed to decode DCS settings", exc_info=True)

        self.logger.info(f"Tesseract path is: {self.editor.prefs.path_tesseract}")
        pytesseract.pytesseract.tesseract_cmd = self.editor.prefs.path_tesseract
        try:
            self.tesseract_version = pytesseract.get_tesseract_version()
        except pytesseract.pytesseract.TesseractNotFoundError:
            self.tesseract_version = None
            PyGUI.Popup("Unable to find tesseract, DCS coordinate capture will be disabled.", title="Error")
        self.logger.info(f"Tesseract version is: {self.tesseract_version}")

        self.window = self.create_gui()


    # ================ profile support


    def load_profile(self, name=None):
        if name is None:
            self.profile = Profile("")
            self.profile.aircraft = self.editor.prefs.airframe_default
        else:
            self.profile = Profile.load(name)
        self.is_profile_dirty = False

    def save_profile(self, name):
        self.profile.save(name)
        self.is_profile_dirty = False

    def profile_names(self):
        return [profile.name for profile in Profile.list_all()]

    def profile_name_for_ui(self):
        if self.profile.profilename == "":
            return "Untitled"
        else:
            return self.profile.profilename

    def import_profile(self, path, csign="", name="", aircraft="viper", warn=False):
        with open(path, "rb") as f:
            data = f.read()
        str = data.decode("UTF-8")
        if CombatFliteXML.is_xml(str):
            if csign != "" and not self.editor.prefs.is_callsign_valid(csign):
                if warn:
                    PyGUI.Popup(f"The callsign '{csign}' is invalid.\n" +
                                 "DCSWE will not use a callsign for this import.", title="Note")
                csign = ""
            profile = CombatFliteXML.profile_from_string(str, csign, name, aircraft)
            if not profile.has_waypoints and warn:
                PyGUI.Popup(f"The profile loaded with no waypoints.\n" +
                             "Are you sure you have a valid callsign set up?", title="Note")
            return profile
        else:
            return Profile.from_string(str)


    # ================ waypoint support


    def find_selected_waypoint(self):
        valuestr = gui_text_unstrike(self.values['ux_prof_wypt_list'][0])
        for wp in self.profile.waypoints:
            if str(wp) == valuestr:
                return wp

    def add_waypoint(self, position, elevation, name=None):
        if name is None:
            name = str()

        try:
            if self.selected_wp_type == "MSN":
                station = int(self.values.get('ux_seq_stn_select', 0))
                number = len(self.profile.stations_dict.get(station, list()))+1
                wp = MSN(position=position, elevation=int(elevation) or 0, name=name,
                         station=station, number=number)

            else:
                sequence = self.values['ux_seq_stn_select']
                if sequence == "None":
                    sequence = 0
                else:
                    sequence = int(sequence)

                if sequence and len(self.profile.get_sequence(sequence)) >= 15:
                    return False

                wp = Waypoint(position, elevation=int(elevation or 0),
                              name=name, sequence=sequence, wp_type=self.selected_wp_type,
                              number=len(self.profile.waypoints_of_type(self.selected_wp_type))+1)

                if sequence not in self.profile.sequences:
                    self.profile.sequences.append(sequence)

            self.profile.waypoints.append(wp)
            self.is_profile_dirty = True
            self.is_waypoint_dirty = False
            # TODO is this right here? should be confined to waypoint list?
            self.update_for_waypoint_list_change()
        except ValueError:
            PyGUI.Popup("Error: missing data or invalid data format.")

        return True


    # ================ ui/ux support


    # instantiate the gui and set it up according to the editor and preferences
    #
    def create_gui(self):
        self.logger.debug("Creating GUI")

        pois = [""] + sorted([poi.name for _, poi in self.editor.default_bases.items()],)
        arfm_ui_text = airframe_type_to_ui_text(self.editor.prefs.airframe_default)
        
        is_dcs_f10_disabled = True if self.tesseract_version is None else False

        # HACK: &@#$* PyGUI forces you to rebuild the entire menu to disable a single item. this also
        # HACK: seems to introduce visual glitches. so, we are going to fall into Tk to do all the
        # HACK: menu handling. build a menu bar with a single menu to get PySimpleGUI to do the right
        # HACK: thing on the layout (we'll delete the menu later).
        #
        menu_bar = PyGUI.MenuBar(["HACK_ME"], key='ux_menubar')

        frame_prof = PyGUI.Frame("Profile",
                                 [[PyGUI.Text("Profile:", size=(8,1), justification="right"),
                                   PyGUI.Combo(values=[""] + self.profile_names(), readonly=True,
                                               enable_events=True, key='ux_prof_select', size=(37,1))],
                                  [PyGUI.Text("Airframe:", size=(8,1), justification="right"),
                                   PyGUI.Combo(values=airframe_list(), default_value=arfm_ui_text,
                                               enable_events=True, key='ux_prof_afrm_select', size=(37,1))],
                                  [PyGUI.Text("Waypoints in Profile:")],
                                  [PyGUI.Listbox(values=list(), size=(48,15),
                                                 enable_events=True, key='ux_prof_wypt_list')],
                                  [PyGUI.Text("Profile has not been modified.", key='ux_prof_state',
                                              size=(24,1)),
                                   PyGUI.Button("Load Profile into Jet", key='ux_prof_enter', size=(17,1),
                                                pad=((10,6),6))]
                                 ])

        frame_coord = PyGUI.Frame("Coordinates",
                                  [[PyGUI.Text("Latitude:", size=(8,1), justification="right"),
                                    PyGUI.InputText(size=(8, 1), key='ux_lat_deg', enable_events=True),
                                    PyGUI.Text("(deg)", pad=((0,12),0)),
                                    PyGUI.InputText(size=(8, 1), key='ux_lat_min', enable_events=True),
                                    PyGUI.Text("(min)", pad=((0,12),0)),
                                    PyGUI.InputText(size=(8, 1), key='ux_lat_sec', enable_events=True),
                                    PyGUI.Text("(sec)", pad=((0,12),0))],
 
                                   [PyGUI.Text("Longitude:", size=(8,1), justification="right"),
                                    PyGUI.InputText(size=(8, 1), key='ux_lon_deg', enable_events=True),
                                    PyGUI.Text("(deg)", pad=((0,12),0)),
                                    PyGUI.InputText(size=(8, 1), key='ux_lon_min', enable_events=True),
                                    PyGUI.Text("(min)", pad=((0,12),0)),
                                    PyGUI.InputText(size=(8, 1), key='ux_lon_sec', enable_events=True),
                                    PyGUI.Text("(sec)", pad=((0,12),0))],
 
                                   [PyGUI.Text("MGRS:", size=(8,1), justification="right", pad=(5,(12,12))),
                                    PyGUI.InputText(size=(25, 1), key='ux_mgrs', enable_events=True)],
 
                                   [PyGUI.Text("Elevation:", size=(8,1), pad=(4,(2,8)), justification="right"),
                                    PyGUI.InputText(size=(8, 1), pad=(6,(2,8)), key='ux_elev_ft',
                                                    enable_events=True),
                                    PyGUI.Text("(ft)", pad=((6,29),(2,8))),
                                    PyGUI.InputText(size=(8, 1), pad=(0,(2,8)), key='ux_elev_m',
                                                    enable_events=True),
                                    PyGUI.Text("(m)", pad=((6,12),(2,8)))]
                                  ])

        frame_capt = PyGUI.Frame("DCS Coordinate Capture",
                                 [[PyGUI.Checkbox("Enable capture from DCS F10 map into", pad=((6,3),6),
                                                  default=False, enable_events=True, key='ux_dcs_f10_enable',
                                                  disabled=is_dcs_f10_disabled),
                                   PyGUI.Combo(values=["Coordiante Panel", "New Waypoint"], size=(18,1),
                                               enable_events=True, key='ux_dcs_f10_tgt_select',
                                               default_value="Coordiante Panel", pad=((0,18),6))],
                                 ])

        frame_wypt = PyGUI.Frame("Waypoint",
                                 [[PyGUI.Text("Set up from predefined location:", pad=(6,(0,16))),
                                   PyGUI.Combo(values=pois, readonly=False, enable_events=True,
                                               key='ux_poi_wypt_select', size=(20,1), pad=(6,(0,16))),
                                   PyGUI.Button(button_text="Filter", size=(6,1), key='ux_poi_filter', pad=(6,(0,16)))],
                                  [PyGUI.Text("Name:", size=(8,1), justification="right"),
                                   PyGUI.InputText(size=(49, 1), key='ux_wypt_name', enable_events=True)],
                                  [PyGUI.Text("Type:", size=(8,1), justification="right"),
                                    PyGUI.Combo(values=["WP", "MSN", "FP", "ST", "IP", "DP", "HA", "HB"],
                                               default_value="WP", enable_events=True, readonly=True,
                                               key='ux_wypt_type_select', size=(8,1))],
                                  [PyGUI.Text("Sequence:", key="ux_seq_sta_text", size=(8,1), justification="right"),
                                   PyGUI.Combo(values=("None", 1, 2, 3), default_value="None",
                                               enable_events=True, readonly=True, key='ux_seq_stn_select',
                                               size=(8,1))],
                                  [frame_coord],
                                  [frame_capt],
                                  [PyGUI.Button("Add", key='ux_wypt_add', size=(14, 1), pad=((6,16),(12,6))),
                                   PyGUI.Button("Update", key='ux_wypt_update', size=(14, 1), pad=((16,16),(12,6))),
                                   PyGUI.Button("Remove", key='ux_wypt_delete', size=(14, 1), pad=((16,6),(12,6)))]
                                 ])

        col_0 = PyGUI.Column([[menu_bar],
                              [frame_prof],
                              [PyGUI.Text(f"Version: {self.dcs_we_version}", pad=(6,12))]],
                             vertical_alignment="top")
        col_1 = PyGUI.Column([[frame_wypt],
                              [PyGUI.Text("Callsign:", size=(8,1), pad=((12,10),12),
                                          justification="right"),
                               PyGUI.InputText(default_text=self.editor.prefs.callsign_default,
                                               key='ux_callsign', enable_events=True, size=(50,1),
                                               pad=(0,6))]],
                             vertical_alignment="top")

        window = PyGUI.Window('DCS Waypoint Editor', [[col_0, col_1]], finalize=True)

        # HACK: build out the two menus on the DCSWE menu bar and install them. they will be populated
        # HACK: with commands as we sync the interface with current state. before doing that, blow away
        # HACK: the hack menu we added for layout purposes.
        #
        menu_bar = window['ux_menubar']
        menu_bar.TKMenu.delete(0,0)
        self.tk_menu_dcswe = tk.Menu(menu_bar.TKMenu, tearoff=False)
        menu_bar.TKMenu.add_cascade(label="DCS WE", menu=self.tk_menu_dcswe, underline=0)
        self.tk_menu_profile = tk.Menu(menu_bar.TKMenu, tearoff=False)
        menu_bar.TKMenu.add_cascade(label="Profile", menu=self.tk_menu_profile, underline=0)
        self.tk_menu_mission = tk.Menu(menu_bar.TKMenu, tearoff=False)
        menu_bar.TKMenu.add_cascade(label="Mission", menu=self.tk_menu_mission, underline=0)

        window['ux_callsign'].bind('<FocusOut>', ':focus_out')

        return window

    # update state in response to a profile change.
    #
    def update_for_profile_change(self, set_to_first=False, update_enable=True):
        profiles = [""] + self.profile_names()
        self.window['ux_prof_select'].update(values=profiles,
                                             set_to_index=profiles.index(self.profile.profilename))
        self.window['ux_poi_wypt_select'].update(set_to_index=0)
        ac_ui_text = airframe_type_to_ui_text(self.profile.aircraft)
        self.window['ux_prof_afrm_select'].update(value=ac_ui_text)
        self.editor.set_driver(self.profile.aircraft)
        if self.is_profile_dirty:
            self.window['ux_prof_state'].update(value="Profile is modified.")
        else:
            self.window['ux_prof_state'].update(value="Profile has not been modified.")
        self.update_for_waypoint_list_change(set_to_first=set_to_first, update_enable=False)
        self.update_for_coords_change()
        self.window['ux_prof_wypt_list'].update(set_to_index=[])
        if update_enable:
            self.update_gui_enable_state()

    # update state in response to changes to the waypoint list.
    #
    def update_for_waypoint_list_change(self, set_to_first=False, update_enable=True):
        values = list()
        self.profile.update_waypoint_numbers()

        for wp in sorted(self.profile.waypoints,
                         key=lambda waypoint: waypoint.wp_type if waypoint.wp_type != "MSN" else str(waypoint.station)):
            namestr = str(wp)
            if not self.editor.driver.validate_waypoint(wp):
                namestr = gui_text_strike(namestr)
            values.append(namestr)

        if set_to_first:
            self.window['ux_prof_wypt_list'].update(values=values, set_to_index=0)
        else:
            self.window['ux_prof_wypt_list'].update(values=values)
        if update_enable:
            self.update_gui_enable_state()

    # update state in response to changes to the waypoint type.
    #
    def update_for_waypoint_type_change(self):
        if self.selected_wp_type == "WP":
            self.window['ux_seq_sta_text'].update(value="Sequence:")
            self.window['ux_seq_stn_select'].update(values=("None", 1, 2, 3), value="None",
                                                            disabled=False, readonly=True)
        elif self.selected_wp_type == "MSN":
            self.window['ux_seq_sta_text'].update(value="Station:")
            self.window['ux_seq_stn_select'].update(values=(8, 7, 3, 2), value=8,
                                                    disabled=False, readonly=True)
        else:
            self.window['ux_seq_sta_text'].update(value="Sequence:")
            self.window['ux_seq_stn_select'].update(values=("None", 1, 2, 3), value="None",
                                                    disabled=True, readonly=False)

    # update state in response to changes in the coordinates.
    #
    def update_for_coords_change(self, position=None, elevation=None, name=None, update_mgrs=True,
                                 wypt_type=None, wypt_seq_sta=None, update_enable=True):
        if position is not None:
            self.window['ux_lat_deg'].update(round(position.lat.degree))
            self.window['ux_lat_min'].update(round(position.lat.minute))
            self.window['ux_lat_sec'].update(round(position.lat.second, 2))

            self.window['ux_lon_deg'].update(round(position.lon.degree))
            self.window['ux_lon_min'].update(round(position.lon.minute))
            self.window['ux_lon_sec'].update(round(position.lon.second, 2))

            mgrs_val = mgrs.encode(mgrs.LLtoUTM(position.lat.decimal_degree, position.lon.decimal_degree), 5)

        else:
            self.window['ux_lat_deg'].update("")
            self.window['ux_lat_min'].update("")
            self.window['ux_lat_sec'].update("")

            self.window['ux_lon_deg'].update("")
            self.window['ux_lon_min'].update("")
            self.window['ux_lon_sec'].update("")

            mgrs_val = ""

        if update_mgrs:
            self.window['ux_mgrs'].update(mgrs_val)

        if elevation is not None:
            self.window['ux_elev_ft'].update(int(float(elevation)))
            self.window['ux_elev_m'].update(int(round(float(elevation)/3.281)))
        else:
            self.window['ux_elev_ft'].update("")
            self.window['ux_elev_m'].update("")
        
        if name is not None:
            self.window['ux_wypt_name'].update(name)
        else:
            self.window['ux_wypt_name'].update("")

        if wypt_type is not None:
            self.selected_wp_type = wypt_type
            self.window['ux_wypt_type_select'].update(value=wypt_type)
            self.update_for_waypoint_type_change()
    
        if wypt_seq_sta is not None:
            self.window['ux_seq_stn_select'].update(value=wypt_seq_sta)
        else:
            self.window['ux_seq_stn_select'].update(value="None")

        if update_enable:
            self.update_gui_enable_state()

        self.window.Refresh()

    # update gui state for menu item enables based on current internal state.
    #
    # HACK: we still have to rebuild the entire menus for some reason (can't get entryconfig to change
    # HACK: state of a single item). however, unlike PySimpleGUI, this approach doesn't have a gnarly
    # HACK: visual artifacts on updates.
    #
    def update_gui_menu_enable_state(self):
        self.tk_menu_dcswe.delete(0, 4)
        self.tk_menu_dcswe.add_command(label='Preferences...', command=self.menu_preferences)
        self.tk_menu_dcswe.add('separator')
        self.tk_menu_dcswe.add_command(label='Check for Updates...', command=self.menu_check_updates)
        self.tk_menu_dcswe.add('separator')
        self.tk_menu_dcswe.add_command(label='Quit', command=self.menu_quit)

        named_prof_norm = 'normal' if self.profile.profilename != "" else 'disabled'
        has_wypt_norm = 'normal' if self.profile.has_waypoints else 'disabled'
        dirty_norm = 'normal' if self.is_profile_dirty else 'disabled'
        if self.dcs_bios_version is not None:
            mission_norm = 'normal' if os.path.exists(self.editor.prefs.path_mission) else 'disabled'
            load_prof_norm = 'normal' if self.profile.has_waypoints else 'disabled'
            install_norm = 'normal'
        else:
            mission_norm = 'disabled'
            load_prof_norm = 'disabled'
            install_norm = 'disabled'
        
        self.tk_menu_profile.delete(0, 12)
        self.tk_menu_profile.add_command(label="New", command=self.menu_profile_new, state=named_prof_norm)
        self.tk_menu_profile.add('separator')
        self.tk_menu_profile.add_command(label='Save...', command=self.menu_profile_save, state=dirty_norm)
        self.tk_menu_profile.add_command(label='Save a Copy As...',
                                         command=self.menu_profile_save_copy, state=named_prof_norm)
        self.tk_menu_profile.add('separator')
        self.tk_menu_profile.add_command(label='Delete...',
                                         command=self.menu_profile_delete, state=named_prof_norm)
        self.tk_menu_profile.add_command(label='Reset Profile Database...',
                                         command=self.menu_profile_reset_db)
        self.tk_menu_profile.add('separator')
        self.tk_menu_profile.add_command(label='Revert', command=self.menu_profile_revert, state=dirty_norm)
        self.tk_menu_profile.add('separator')

        submenu_import = tk.Menu(self.tk_menu_profile, tearoff=False)
        self.tk_menu_profile.add_command(label="Load Profile into Jet",
                                         command=self.menu_profile_load_jet, state=load_prof_norm)
        self.tk_menu_profile.add_cascade(label="Import", menu=submenu_import, underline=0)
        submenu_import.add_command(label="From Clipboard as Encoded DCSWE JSON",
                                   command=self.menu_profile_import_from_encoded_string)
        submenu_import.add_command(label="From CombatFlite XML or DCSWE JSON File...",
                                   command=self.menu_profile_import_from_file)

        submenu_export = tk.Menu(self.tk_menu_profile, tearoff=False)
        self.tk_menu_profile.add_cascade(label="Export", menu=submenu_export, underline=0)
        submenu_export.add_command(label="To Clipboard as Encoded DCSWE JSON",
                                   command=self.menu_profile_export_to_enc_string, state=has_wypt_norm)
        submenu_export.add_command(label="To Clipboard as Text",
                                   command=self.menu_profile_export_to_pln_string, state=has_wypt_norm)
        submenu_export.add_command(label="To DCSWE JSON File...",
                                   command=self.menu_profile_export_to_file, state=has_wypt_norm)

        self.tk_menu_mission.delete(0,2)
        self.tk_menu_mission.add_command(label="Install Mission Package...",
                                         command=self.menu_mission_install_package, state=install_norm)
        self.tk_menu_mission.add('separator')
        self.tk_menu_mission.add_command(label="Load Mission File into Jet",
                                         command=self.menu_mission_load_jet, state=mission_norm)

    # update gui state for control enables based on current internal state.
    #
    def update_gui_control_enable_state(self):
        if self.is_dcs_f10_enabled == True and self.tesseract_version is not None:
            self.window['ux_dcs_f10_tgt_select'].update(disabled=False, readonly=True)
        else:
            self.window['ux_dcs_f10_tgt_select'].update(disabled=True, readonly=False)

        if self.is_dcs_f10_tgt_add:
            self.window['ux_dcs_f10_tgt_select'].update(set_to_index=1)
        else:
            self.window['ux_dcs_f10_tgt_select'].update(set_to_index=0)

        if self.profile.has_waypoints == True:
            if self.dcs_bios_version is not None:
                self.window['ux_prof_enter'].update(disabled=False)
            else:
                self.window['ux_prof_enter'].update(disabled=True)
        else:
            self.window['ux_prof_enter'].update(disabled=True)

        posn, elev, _ = self.validate_coords()
        if posn is not None and elev is not None:
            self.window['ux_wypt_add'].update(disabled=False)
        else:
            self.window['ux_wypt_add'].update(disabled=True)

        if len(self.window['ux_prof_wypt_list'].get()) > 0:
            if self.is_waypoint_dirty:
                self.window['ux_wypt_update'].update(disabled=False)
            else:
                self.window['ux_wypt_update'].update(disabled=True)
            self.window['ux_wypt_delete'].update(disabled=False)
        else:
            self.window['ux_wypt_update'].update(disabled=True)
            self.window['ux_wypt_delete'].update(disabled=True)

    # update the gui enable state for changes to internal state
    #
    def update_gui_enable_state(self):
        self.update_gui_control_enable_state()
        self.update_gui_menu_enable_state()

    # update the coordinates elements enable/disable state
    #
    def update_gui_coords_input_disabled(self, disabled):
        for element_name in ('ux_lat_deg', 'ux_lat_min', 'ux_lat_sec', 'ux_lon_deg', 'ux_lon_min',
                             'ux_lon_sec', 'ux_mgrs', 'ux_elev_ft', 'ux_elev_m'):
            self.window.Element(element_name).update(disabled=disabled)

    # change the binding of a hotkey. providing only previous will unbind the key.
    #
    # to change the callback, first unbind, then rebind.
    #
    def rebind_hotkey(self, previous, current=None, callback=None):
        try:
            if previous is not current:
                self.logger.debug(f"Rebinding hotkey from '{previous}' to '{current}'")
                if previous is not None and previous != "":
                    keyboard.remove_hotkey(previous)
                if current is not None and current != "" and callback is not None:
                    keyboard.add_hotkey(current, callback)
        except KeyError:
            self.logger.debug(f"Cannot change hotkey binding from '{previous}' to '{current}'")

    # validate coordinates in ui. returns an {position, elevation, name} tuple; None's if invalid
    #
    def validate_coords(self):
        lat_deg = self.window['ux_lat_deg'].get()
        lat_min = self.window['ux_lat_min'].get()
        lat_sec = self.window['ux_lat_sec'].get()

        lon_deg = self.window['ux_lon_deg'].get()
        lon_min = self.window['ux_lon_min'].get()
        lon_sec = self.window['ux_lon_sec'].get()

        try:
            position = LatLon(Latitude(degree=lat_deg, minute=lat_min, second=lat_sec),
                              Longitude(degree=lon_deg, minute=lon_min, second=lon_sec))
            elevation = int(self.window['ux_elev_ft'].get())
            name = self.window['ux_wypt_name'].get()
            return position, elevation, name
        except ValueError as e:
            if lat_deg != "" or lat_min != "" or lat_sec != "" or \
               lon_deg != "" or lon_min != "" or lon_sec != "":
                self.logger.error(f"Failed to validate coords: {e}")
            return None, None, None


    # ================ ui menu item handlers


    # HACK: menu items, unlike other handlers, are called directly from Tk outside of PySimpleGUI.
    # HACK: to keep things kinda like PySimpleGUI, the command handlers will enqueue operations on
    # HACK: a pending menu command queue so that the main loop can invoke the actual handler.

    def menu_preferences(self):
        self.menu_pend_q.put(self.do_menu_preferences)

    def menu_check_updates(self):
        self.menu_pend_q.put(self.do_menu_check_updates)
    
    def menu_quit(self):
        self.menu_pend_q.put(self.do_menu_quit)

    def menu_profile_new(self):
        self.menu_pend_q.put(self.do_menu_profile_new)

    def menu_profile_save(self):
        self.menu_pend_q.put(self.do_menu_profile_save)

    def menu_profile_save_copy(self):
        self.menu_pend_q.put(self.do_menu_profile_save_copy)

    def menu_profile_delete(self):
        self.menu_pend_q.put(self.do_menu_profile_delete)
    
    def menu_profile_reset_db(self):
        self.menu_pend_q.put(self.do_menu_profile_reset_db)

    def menu_profile_revert(self):
        self.menu_pend_q.put(self.do_menu_profile_revert)

    def menu_profile_load_jet(self):
        self.menu_pend_q.put(self.do_hk_profile_enter_in_jet)

    def menu_profile_export_to_enc_string(self):
        self.menu_pend_q.put(self.do_menu_profile_export_to_enc_string)

    def menu_profile_export_to_pln_string(self):
        self.menu_pend_q.put(self.do_menu_profile_export_to_pln_string)

    def menu_profile_export_to_file(self):
        self.menu_pend_q.put(self.do_menu_profile_export_to_file)

    def menu_profile_import_from_encoded_string(self):
        self.menu_pend_q.put(self.do_menu_profile_import_from_encoded_string)

    def menu_profile_import_from_file(self):
        self.menu_pend_q.put(self.do_menu_profile_import_from_file)

    def menu_mission_install_package(self):
        self.menu_pend_q.put(self.do_menu_mission_install_package)
    
    def menu_mission_load_jet(self):
        self.menu_pend_q.put(self.do_hk_mission_enter_in_jet)


    def do_menu_preferences(self):
        prefs = self.editor.prefs
        hk_capture = prefs.hotkey_capture
        hk_capture_mode = prefs.hotkey_capture_mode
        hk_enter_profile = prefs.hotkey_enter_profile
        hk_enter_mission = prefs.hotkey_enter_mission

        prefs_gui = DCSWEPreferencesGUI(prefs)
        prefs_gui.run()

        if self.profile.profilename == "":
            self.profile.aircraft = prefs.airframe_default
            self.update_for_profile_change()

        self.dcs_bios_version = dcs_bios_vers_install(prefs.path_dcs)

        if self.is_dcs_f10_enabled:
            self.rebind_hotkey(hk_capture, prefs.hotkey_capture, self.hkey_dcs_f10_capture)
            self.rebind_hotkey(hk_capture_mode, prefs.hotkey_capture_mode, self.hkey_dcs_f10_capture_tgt_toggle)
        else:
            self.rebind_hotkey(hk_capture)
            self.rebind_hotkey(hk_capture_mode)
        self.rebind_hotkey(hk_enter_profile, prefs.hotkey_enter_profile, self.hkey_profile_enter_in_jet)
        self.rebind_hotkey(hk_enter_mission, prefs.hotkey_enter_mission, self.hkey_mission_enter_in_jet)

        self.update_gui_enable_state()
    
    def do_menu_check_updates(self):
        path_dcs = self.editor.prefs.path_dcs
        is_db_current = dcs_bios_is_current(path_dcs)
        is_we_current = dcs_we_is_current()
        if is_db_current == True and is_we_current == True:
            PyGUI.Popup("DCS Waypoint Editor and DCS-BIOS are up-to-date.",
                        title="No Updates Available")
        else:
            if is_db_current == False and is_we_current == False:
                PyGUI.Popup("There are new versions availble of both DCS Waypoint Editor and DCS-BIOS.",
                            title="Updates Available")
            vers_sw_cur = dcs_we_vers_install()
            vers_sw_latest = dcs_we_vers_latest()
            sw_install_fn = lambda: dcs_we_install()
            if gui_update_request("DCS Waypoint Editor", vers_sw_cur, vers_sw_latest, sw_install_fn):
                self.window.close()
            vers_db_cur = dcs_bios_vers_install(path_dcs)
            vers_db_latest = dcs_bios_vers_latest()
            db_install_fn = lambda: dcs_bios_install(path_dcs)
            gui_update_request("DCS-BIOS", vers_db_cur, vers_db_latest, db_install_fn)

    def do_menu_quit(self):
        self.window.close()

    def do_menu_profile_new(self):
        self.load_profile()
        self.update_for_profile_change()

    def do_menu_profile_save(self):
        name = self.profile.profilename
        if name == "":
            name = PyGUI.PopupGetText("Profile Name", "Saving New Profile")
            if name is None or len(name) == 0:
                name = None
            elif len([obj for obj in Profile.list_all() if obj.name == name]) != 0:
                PyGUI.Popup(f"There is already a profile named '{name}'.", title="Error")
                name = None
        if name is not None:
            self.save_profile(name)
            self.update_for_profile_change()

    def do_menu_profile_save_copy(self):
        if self.profile.profilename == "":
            name = PyGUI.PopupGetText("Profile Name", "Saving New Profile")
        else:
            name = PyGUI.PopupGetText("Profile Name", "Copying Existing Profile")
        if name is not None and len(name) > 0:
            if len([obj for obj in Profile.list_all() if obj.name == name]) == 0:
                self.save_profile(name)
                self.update_for_profile_change()
            else:
                PyGUI.Popup(f"There is already a profile named '{name}'.", title="Error")

    def do_menu_profile_delete(self):
        if self.profile.profilename != "":
            result = PyGUI.PopupOKCancel(f"Are you sure you want to delete the profile" +
                                         f" '{self.profile.profilename}'?", title="Say Intentions")
            if result == "OK":
                Profile.delete(self.profile.profilename)
                self.load_profile()
                self.update_for_profile_change()

    def do_menu_profile_reset_db(self):
        if PyGUI.PopupOKCancel(f"Are you sure you want to delete the profile database? This will" +
                               " remove all profiles.", title="Say Intentions") == "OK":
            self.editor.reset_db()
            self.load_profile()
            self.update_for_profile_change()

    def do_menu_profile_revert(self):
        self.load_profile(self.profile.profilename)
        self.update_for_profile_change()

    # exports profile to clipboard as a zip'd JSON encoded in ASCII
    #
    def do_menu_profile_export_to_enc_string(self):
        name = self.profile_name_for_ui()
        encoded = json_zip(str(self.profile))
        pyperclip.copy(encoded)
        PyGUI.Popup(f"Profile '{name}' copied as encoded text to clipboard.")

    # exports profile to clipboard as a human-readable string
    #
    def do_menu_profile_export_to_pln_string(self):
        name = self.profile_name_for_ui()
        profile_string = self.profile.to_readable_string()
        pyperclip.copy(profile_string)
        PyGUI.Popup(f"Profile '{name}' copied as plain text to clipboard.")

    # exports profile to file as JSON
    #
    def do_menu_profile_export_to_file(self):
        name = self.profile_name_for_ui()
        filename = PyGUI.PopupGetFile("Specify a File to Export To",
                                      f"Exporting Profile '{name}' from Database",
                                      default_extension=".json", save_as=True,
                                      file_types=(("JSON File", "*.json"),))
        if filename is not None:
            with open(filename + ".json", "w+") as f:
                f.write(str(self.profile))
            PyGUI.Popup(f"Profile '{name}' successfullly written to '{filename}'.")

    # imports profile from zip'd JSON encoded as ASCII on clipboard into empty/new profile
    #
    def do_menu_profile_import_from_encoded_string(self):
        encoded = pyperclip.paste()
        try:
            self.profile = Profile.from_string(json_unzip(encoded))
            #
            # note that encoded JSON may carry profile name, we will force the name to the name of
            # the empty slot, "" here.
            #
            self.profile.profilename = ""
            if self.profile.aircraft is None:
                self.profile.aircraft = self.editor.prefs.airframe_default
            self.is_profile_dirty = True
            self.window['ux_prof_select'].update(set_to_index=0)
            self.update_for_profile_change(set_to_first=True)
            self.logger.debug(self.profile.to_dict())
        except Exception as e:
            PyGUI.Popup("Failed to parse encoded profile from clipboard.")
            self.logger.error(e, exc_info=True)

    # imports profile from text JSON or combatflite XML file into empty/new profile
    #
    def do_menu_profile_import_from_file(self):
        filename = PyGUI.PopupGetFile("Select a File to Import From", "Importing Profile from File")
        if filename is not None:
            try:
                self.validate_text_callsign('ux_callsign')
                self.profile = self.import_profile(filename, warn=True,
                                                   csign=self.editor.prefs.callsign_default,
                                                   aircraft=self.editor.prefs.airframe_default)
                #
                # note that text JSON may carry profile name, we will force the name to the name of the
                # empty slot, "" here.
                #
                self.profile.profilename = ""
                if self.profile.aircraft is None:
                    self.profile.aircraft = self.editor.prefs.airframe_default
                self.is_profile_dirty = True
                self.window['ux_prof_select'].update(set_to_index=0)
                self.update_for_profile_change(set_to_first=True)
                self.logger.debug(self.profile.to_dict())
            except:
                PyGUI.Popup(f"Unable to parse the file '{filename}'", title="Error")

    def do_menu_mission_install_package(self):
        try:
            self.validate_text_callsign('ux_callsign')
            callsign = self.editor.prefs.callsign_default
            if callsign == "":
                raise ValueError("Empty callsign")
        except:
            PyGUI.Popup(f"Mission package installation requires a valid, non-empty callsign.",
                        title="Error")
            return
        airframe_ui = self.window['ux_prof_afrm_select'].get()
        airframe = airframe_ui_text_to_type(airframe_ui)
        mpack_path = PyGUI.PopupGetFile("Select a Mission Package to Install",
                                        f"Installing Package for {airframe_ui} {callsign}",
                                        file_types=(("Zip File", "*.zip"),))
        if mpack_path is not None:
            mpack_name, _ = os.path.splitext(mpack_path)
            mpack_name = ((os.path.split(mpack_name))[1]).replace(" ", "-")

            if mpack_name in self.profile_names() and \
               PyGUI.PopupOKCancel(f"There is already a profile named '{mpack_name}'. Replace it?",
                                   title="Duplicate Profile Name") == "Cancel":
                return

            try:
                dcs_path = self.editor.prefs.path_dcs
                profile = dcswe_install_mpack(mpack_path, mpack_name, airframe, callsign, dcs_path)
                profile.save(profile.profilename)
                self.load_profile(profile.profilename)
                self.window['ux_prof_select'].update(value=profile.profilename)
                self.update_for_profile_change(set_to_first=True)
            except Exception as e:
                filename = (os.path.split(mpack_path))[1]
                PyGUI.Popup(f"Unable to install the mission package '{filename}': {e}", title="Error")


    # ================ ui profile panel handlers


    def do_profile_select(self):
        try:
            profile_name = self.values['ux_prof_select']
            self.load_profile(profile_name)
        except DoesNotExist:
            PyGUI.Popup(f"Profile '{profile_name}' was not found in the database.", title="Error")
            self.load_profile()
        self.update_for_profile_change(set_to_first=True)

    def do_airframe_select(self):
        airframe_type = airframe_ui_text_to_type(self.values['ux_prof_afrm_select'])
        self.profile.aircraft = airframe_type
        self.is_profile_dirty = True
        self.update_for_profile_change()

    def do_profile_enter_in_jet(self):
        if gui_verify_dcs_running("Unable to enter the profile into the jet. ") and \
           self.dcs_bios_version is not None and self.profile.has_waypoints:
            self.logger.info(f"Entering profile '{self.profile_name_for_ui()}' into jet...")
            self.window['ux_prof_enter'].update(disabled=True)
            profile_name = self.profile_name_for_ui()
            airframe = self.window['ux_prof_afrm_select'].get()
            gui_backgrounded_operation(f"Entering Profile '{profile_name}' into {airframe}...",
                                       bop_fn=self.editor.enter_all, bop_args=(self.profile,))
            self.window['ux_prof_enter'].update(disabled=False)
            self.update_gui_enable_state()
        else:
            winsound.PlaySound(UX_SND_ERROR, flags=winsound.SND_FILENAME)

    def do_profile_waypoint_list(self):
        if self.values['ux_prof_wypt_list']:
            wypt = self.find_selected_waypoint()
            if wypt.wp_type == "MSN":
                seq_stn = wypt.station
            elif wypt.wp_type == "WPT":
                seq_stn = wypt.Sequence
            else:
                seq_stn = None
            self.is_waypoint_dirty = False
            self.update_for_coords_change(wypt.position, wypt.elevation, wypt.name, wypt_type=wypt.wp_type,
                                          wypt_seq_sta=seq_stn)


    # ================ ui waypoint panel handlers


    def do_wypt_name(self):
        self.is_waypoint_dirty = True
        self.update_gui_control_enable_state()

    def do_wypt_type_select(self):
        self.selected_wp_type = self.values['ux_wypt_type_select']
        self.is_waypoint_dirty = True
        self.update_for_waypoint_type_change()
        self.update_gui_control_enable_state()

    def do_seq_stn_select(self):
        self.is_waypoint_dirty = True
        self.update_gui_control_enable_state()

    def do_poi_wypt_select(self):
        poi = self.editor.default_bases.get(self.values['ux_poi_wypt_select'])
        if poi is not None:
            self.is_waypoint_dirty = True
            self.update_for_coords_change(poi.position, poi.elevation, poi.name)

    def do_dcs_f10_tgt_select(self):
        if self.is_dcs_f10_enabled:
            if self.values['ux_dcs_f10_tgt_select'] == "Coordiante Panel":
                self.is_dcs_f10_tgt_add = False
            else:
                self.is_dcs_f10_tgt_add = True

    def do_poi_wypt_filter(self):
        text = self.values['ux_poi_wypt_select']
        self.window['ux_poi_wypt_select'].\
            update(values=[""] + [poi.name for _, poi in self.editor.default_bases.items() if
                                  text.lower() in poi.name.lower()],
                   set_to_index=0)

    def do_waypoint_add(self):
        position, elevation, name = self.validate_coords()
        if position is not None:
            self.add_waypoint(position, elevation, name)
            self.is_waypoint_dirty = False
        else:
            PyGUI.Popup("Cannot add waypoint without coordinates.")
        self.window['ux_poi_wypt_select'].update(set_to_index=0)
        # TODO is this right here? should be confined to waypoint list?
        self.update_for_profile_change()

    def do_waypoint_update(self):
        if self.values['ux_prof_wypt_list']:
            waypoint = self.find_selected_waypoint()
            position, elevation, name = self.validate_coords()
            if position is not None:
                waypoint.position = position
                waypoint.elevation = elevation
                waypoint.name = name
                self.is_waypoint_dirty = False
                self.is_profile_dirty = True
            else:
                PyGUI.Popup("Cannot update waypoint without coordinates.")
        self.window['ux_poi_wypt_select'].update(set_to_index=0)
        self.update_for_waypoint_list_change()

    def do_waypoint_delete(self):
        if self.values['ux_prof_wypt_list']:
            valuestr = gui_text_unstrike(self.values['ux_prof_wypt_list'][0])
            for wp in self.profile.waypoints:
                if str(wp) == valuestr:
                    self.profile.waypoints.remove(wp)
                    self.is_waypoint_dirty = False
                    self.is_profile_dirty = True
            self.update_for_profile_change()
        self.window['ux_poi_wypt_select'].update(set_to_index=0)

    def do_dcs_f10_enable(self):
        self.is_dcs_f10_enabled = self.values['ux_dcs_f10_enable']
        if self.is_dcs_f10_enabled:
            self.rebind_hotkey(None, self.editor.prefs.hotkey_capture, self.hkey_dcs_f10_capture)
            self.rebind_hotkey(None, self.editor.prefs.hotkey_capture_mode, self.hkey_dcs_f10_capture_tgt_toggle)
        else:
            self.rebind_hotkey(self.editor.prefs.hotkey_capture)
            self.rebind_hotkey(self.editor.prefs.hotkey_capture_mode)
        self.update_gui_enable_state()

    # update ui state of widgets linked to a change in elevation (ft)
    #
    def do_waypoint_linked_update_elev_ft(self):
        try:
            elevation = float(self.values['ux_elev_ft'])
            self.window['ux_elev_m'].update(round(elevation/3.281))
        except:
            self.window['ux_elev_m'].update("")
        self.is_waypoint_dirty = True
        self.update_gui_enable_state()

    # update ui state of widgets linked to a change in elevation (m)
    #
    def do_waypoint_linked_update_elev_m(self):
        try:
            elevation = float(self.values['ux_elev_m'])
            self.window['ux_elev_ft'].update(round(elevation*3.281))
        except:
            self.window['ux_elev_ft'].update("")
        self.is_waypoint_dirty = True
        self.update_gui_enable_state()

    # update ui state of widgets linked to a change in mgrs
    #
    def do_waypoint_linked_update_mgrs(self):
        position, _, _ = self.validate_coords()
        if position is not None:
            m = mgrs.encode(mgrs.LLtoUTM(position.lat.decimal_degree, position.lon.decimal_degree), 5)
            self.window['ux_mgrs'].update(m)
            self.is_waypoint_dirty = True
        self.update_gui_enable_state()

    # update ui state of widgets linked to a change in position (lat/lon)
    #
    def do_waypoint_linked_update_position(self):
        mgrs_str = self.values['ux_mgrs']
        if mgrs_str is not None:
            try:
                decoded_mgrs = mgrs.UTMtoLL(mgrs.decode(mgrs_str.replace(" ", "")))
                position = LatLon(Latitude(degree=decoded_mgrs["lat"]), Longitude(degree=decoded_mgrs["lon"]))
                self.is_waypoint_dirty = True
                self.update_for_coords_change(position, update_mgrs=False)
            except (TypeError, ValueError, UnboundLocalError) as e:
                PyGUI.Popup(f"Cannot decode MGRS '{mgrs_str}', {e}")


    # ================ ui miscellaneous controls


    def do_callsign(self):
        return


    # ================ keyboard hotkey handlers


    # as these are not typically called form the run loop (as they represent hotkeys and so on that
    # might not have widgets), we pend hotkeys onto hkey_pend_q via hkey_<foo> and do the work on
    # the main thread via do_hk_<foo>.

    def hkey_clear_pendings(self):
        with self.menu_pend_q.mutex:
            self.menu_pend_q.queue.clear()

    def hkey_dcs_f10_capture(self):
        self.hkey_pend_q.put(self.do_hk_dcs_f10_capture)
    
    def hkey_dcs_f10_capture_tgt_toggle(self):
        self.hkey_pend_q.put(self.do_hk_dcs_f10_capture_tgt_toggle)
 
    def hkey_profile_enter_in_jet(self):
        self.hkey_pend_q.put(self.do_hk_profile_enter_in_jet)

    def hkey_mission_enter_in_jet(self):
        self.hkey_pend_q.put(self.do_hk_mission_enter_in_jet)


    def do_hk_dcs_f10_capture(self):
        self.logger.info(f"DCS F10 capture map is_dcs_f10_tgt_add {self.is_dcs_f10_tgt_add}")
        self.update_gui_coords_input_disabled(True)
        try:
            is_debug = True if self.editor.prefs.is_tesseract_debug_bool else False
            captured_coords = dcs_f10_capture_map_coords(scaled_dcs_gui=self.scaled_dcs_gui,
                                                         is_debug=is_debug)
            position, elevation = dcs_f10_parse_map_coords_string(captured_coords)
            if position is None:
                raise ValueError("Capture or parse fails")
            if self.is_dcs_f10_tgt_add:
                if self.add_waypoint(position, elevation) is None:
                    raise ValueError("Adding captured waypoint fails")
            else:
                self.update_for_coords_change(position, elevation, update_mgrs=True, update_enable=False)
                self.do_waypoint_linked_update_elev_ft()
            winsound.PlaySound(UX_SND_F10CAP_GOT_WAYPT, flags=winsound.SND_FILENAME)
        except (IndexError, ValueError, TypeError):
            winsound.PlaySound(UX_SND_ERROR, flags=winsound.SND_FILENAME)
        self.update_gui_coords_input_disabled(False)
        self.update_for_waypoint_list_change()

    def do_hk_dcs_f10_capture_tgt_toggle(self):
        self.logger.info(f"Toggling DCS F10 map capture target, was {self.is_dcs_f10_tgt_add}")
        self.is_dcs_f10_tgt_add = not self.is_dcs_f10_tgt_add
        winsound.PlaySound(UX_SND_F10CAP_TOGGLE_MODE, flags=winsound.SND_FILENAME)
        if self.is_dcs_f10_tgt_add:
            winsound.PlaySound(UX_SND_F10CAP_TOGGLE_MODE, flags=winsound.SND_FILENAME)
        self.update_gui_enable_state()

    def do_hk_profile_enter_in_jet(self):
        if self.dcs_bios_version is not None:
            winsound.PlaySound(UX_SND_INJECT_TO_JET, flags=winsound.SND_FILENAME)
            winsound.PlaySound(UX_SND_INJECT_TO_JET, flags=winsound.SND_FILENAME)
            self.do_profile_enter_in_jet()
            #
            # ditch hotkeys that came in while we were away.
            #
            self.hkey_clear_pendings()
        else:
            winsound.PlaySound(UX_SND_ERROR, flags=winsound.SND_FILENAME)

    def do_hk_mission_enter_in_jet(self):
        if gui_verify_dcs_running("Unable to enter the mission into the jet. ") and \
           self.dcs_bios_version is not None:
            mission_name = (os.path.split(self.editor.prefs.path_mission))[1]
            self.logger.info(f"Entering mission '{mission_name}' into jet...")
            self.window['ux_prof_enter'].update(disabled=True)
            try:
                self.validate_text_callsign('ux_callsign')
                tmp_profile = self.import_profile(self.editor.prefs.path_mission,
                                                  csign=self.editor.prefs.callsign_default,
                                                  aircraft=self.editor.prefs.airframe_default)
                winsound.PlaySound(UX_SND_INJECT_TO_JET, flags=winsound.SND_FILENAME)
                if tmp_profile.has_waypoints:
                    tmp_profile.aircraft = self.editor.prefs.airframe_default
                    self.editor.set_driver(tmp_profile.aircraft)
                    airframe = airframe_type_to_ui_text(tmp_profile.aircraft)
                    gui_backgrounded_operation(f"Entering Mission '{mission_name}' into {airframe}...",
                                               bop_fn=self.editor.enter_all, bop_args=(tmp_profile,))
                    self.editor.set_driver(self.profile.aircraft)
                    #
                    # ditch hotkeys that came in while we were away.
                    #
                    self.hkey_clear_pendings()
                else:
                    winsound.PlaySound(UX_SND_ERROR, flags=winsound.SND_FILENAME)
            except:
                winsound.PlaySound(UX_SND_ERROR, flags=winsound.SND_FILENAME)
            self.update_gui_enable_state()
        else:
            winsound.PlaySound(UX_SND_ERROR, flags=winsound.SND_FILENAME)


    # ================ text field validation


    def validate_text_callsign(self, event):
        callsign = self.window[event].get()
        try:
            self.editor.prefs.callsign_default = callsign
            self.editor.prefs.persist_prefs()
            return None
        except:
            return "Invalid callsign.\nCallsigns must be of the form \"Witcher1-1\"."


    # ================ ui main loop


    def run(self):
        if self.dcs_bios_version is None:
            PyGUI.Popup("DCS-BIOS not detected. Some functionality will not be available.", title="Note")

        if self.is_dcs_f10_enabled:
            self.rebind_hotkey(None, self.editor.prefs.hotkey_capture, self.hkey_dcs_f10_capture)
            self.rebind_hotkey(None, self.editor.prefs.hotkey_capture_mode, self.hkey_dcs_f10_capture_tgt_toggle)
        self.rebind_hotkey(None, self.editor.prefs.hotkey_enter_profile, self.hkey_profile_enter_in_jet)
        self.rebind_hotkey(None, self.editor.prefs.hotkey_enter_mission, self.hkey_mission_enter_in_jet)

        self.update_for_profile_change()

        # the handler map includes only those controls managed by PySimpleGUI

        handler_map = { 'ux_prof_select' : self.do_profile_select,
                        'ux_prof_afrm_select' : self.do_airframe_select,

                        'ux_prof_enter' : self.do_profile_enter_in_jet,

                        'ux_prof_wypt_list' : self.do_profile_waypoint_list,

                        'ux_wypt_name' : self.do_wypt_name,
                        'ux_wypt_type_select' : self.do_wypt_type_select,
                        'ux_seq_stn_select' : self.do_seq_stn_select,
                        'ux_poi_wypt_select' : self.do_poi_wypt_select,
                        'ux_dcs_f10_tgt_select' : self.do_dcs_f10_tgt_select,
                        'ux_poi_filter' : self.do_poi_wypt_filter,

                        'ux_wypt_add': self.do_waypoint_add,
                        'ux_wypt_update': self.do_waypoint_update,
                        'ux_wypt_delete': self.do_waypoint_delete,
                        'ux_dcs_f10_enable': self.do_dcs_f10_enable,

                        'ux_elev_ft' : self.do_waypoint_linked_update_elev_ft,
                        'ux_elev_m' : self.do_waypoint_linked_update_elev_m,
                        'ux_lat_deg' : self.do_waypoint_linked_update_mgrs,
                        'ux_lat_min' : self.do_waypoint_linked_update_mgrs,
                        'ux_lat_sec' : self.do_waypoint_linked_update_mgrs,
                        'ux_lon_deg' : self.do_waypoint_linked_update_mgrs,
                        'ux_lon_min' : self.do_waypoint_linked_update_mgrs,
                        'ux_lon_sec' : self.do_waypoint_linked_update_mgrs,

                        'ux_mgrs' : self.do_waypoint_linked_update_position,

                        'ux_callsign' : self.do_callsign
         }
        validate_map = { 'ux_callsign:focus_out' : self.validate_text_callsign }

        while True:
            event, self.values = self.window.Read(timeout=100, timeout_key='Timeout')
            if event != 'Timeout':
                self.logger.debug(f"DCSWE Event: {event}")
                self.logger.debug(f"DCSWE Values: {self.values}")
                try:
                    err_msg = (validate_map[event])(event.split(":")[0])
                    if err_msg is not None:
                        PyGUI.Popup(err_msg, title="Error")
                except:
                    pass

            if event is None or event == 'Exit' or event == PyGUI.WIN_CLOSED:
                self.logger.info("Exiting...")
                break

            # ======== hotkeys, menus (enqueued from handler outside PySimpleGUI)

            elif event == 'Timeout':
                while True:
                    try:
                        hkey_callback = self.hkey_pend_q.get(False)
                        self.logger.debug(f"DCSWE hkey callback: {hkey_callback}")
                        err_msg = hkey_callback()
                        if err_msg is not None:
                            PyGUI.Popup(err_msg, title="Error")
                            with self.hkey_pend_q.mutex:
                                self.hkey_pend_q.clear()
                    except queue.Empty:
                        break

                # to handle validation correctly, prior to triggering a menu command, force a focus_out
                # on the current element.
                #
                if not self.menu_pend_q.empty() and self.window.find_element_with_focus() is not None:
                    self.window.force_focus()
                else:
                    while True:
                        try:
                            menu_callback = self.menu_pend_q.get(False)
                            self.logger.debug(f"DCSWE menu callback: {menu_callback}")
                            menu_callback()
                        except queue.Empty:
                            break

            # ======== ui handlers

            else:
                try:
                    (handler_map[event])()
                except:
                    pass

        self.close()

    def close(self):
        self.validate_text_callsign('ux_callsign')

        self.rebind_hotkey(self.editor.prefs.hotkey_capture)
        self.rebind_hotkey(self.editor.prefs.hotkey_capture_mode)
        self.rebind_hotkey(self.editor.prefs.hotkey_enter_profile)
        self.rebind_hotkey(self.editor.prefs.hotkey_enter_mission)

        self.window.close()

        self.editor.stop()
