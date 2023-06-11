'''
*
*  prefs_gui.py: DCS Waypoint Editor preferences GUI
*
*  Copyright (C) 2021-23 twillis/ilominar
*
*  This program is free software: you can redistribute it and/or modify
*  it under the terms of the GNU General Public License as published by
*  the Free Software Foundation, either version 3 of the License, or
*  (at your option) any later version.
*
*  This program is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*  GNU General Public License for more details.
*
*  You should have received a copy of the GNU General Public License
*  along with this program.  If not, see <https://www.gnu.org/licenses/>.
*
'''

import os
import PySimpleGUI as PyGUI
from PySimpleGUI.PySimpleGUI import PopupOKCancel, T
import requests

from src.comp_dcs_bios import dcs_bios_vers_install, dcs_bios_vers_latest, dcs_bios_is_current
from src.comp_dcs_bios import dcs_bios_install
from src.db_models import AvionicsSetupModel
from src.gui_util import airframe_list, airframe_ui_text_to_type, airframe_type_to_ui_text
from src.logger import get_logger


class PreferencesGUI:
    def __init__(self, prefs):
        self.prefs = prefs

        self.logger = get_logger(__name__)
        self.values = None
        self.window = self.create_gui()

    # persist valid preferences to settings.ini based on values extracted from the prefs window.
    # returns string CSV list of prefs with errors, None if no errors.
    #
    def prefs_persist(self, values):
        self.logger.info("Persisting preferences...")
        errors = ""

        path_dcs = values.get('ux_path_dcs')
        if path_dcs is not None and not path_dcs.endswith("\\") and not path_dcs.endswith("/"):
            path_dcs = path_dcs + "\\"
        if path_dcs is not None and os.path.exists(path_dcs):
            self.prefs.path_dcs = values.get('ux_path_dcs')
        else:
            errors = errors + "DCS path, "

        path_tesseract = values.get('ux_path_tesseract')
        if path_tesseract is not None and os.path.exists(path_tesseract):
            self.prefs.path_tesseract = values.get('ux_path_tesseract')
        else:
            errors = errors + "Tesseract path, "

        self.prefs.path_mission = values.get('ux_path_mission')

        try:
            self.prefs.airframe_default = airframe_ui_text_to_type(values.get('ux_airframe_default'))
        except:
            errors = errors + "default airframe, "

        try:
            self.prefs.av_setup_default = values.get('ux_av_setup_default')
            if self.prefs.av_setup_default not in AvionicsSetupModel.list_all_names():
                raise Exception("Unknown avionics setup")
        except:
            self.prefs.av_setup_default = "DCS Default, "

        try:
            self.prefs.dcs_btn_rel_delay_short = values.get('ux_dcs_btn_rel_delay_short')
        except:
            errors = errors + "short release, "

        try:
            self.prefs.dcs_btn_rel_delay_medium = values.get('ux_dcs_btn_rel_delay_medium')
        except:
            errors = errors + "medium release, "

        try:
            self.prefs.hotkey_capture = values.get('ux_hotkey_capture')
        except:
            errors = errors + "'F10 Capture' hotkey, "

        try:
            self.prefs.hotkey_capture_mode = values.get('ux_hotkey_capture_mode')
        except:
            errors = errors + "'F10 Capture Mode' hotkey, "

        try:
            self.prefs.hotkey_enter_profile = values.get('ux_hotkey_enter_profile')
        except:
            errors = errors + "'Load Profile' hotkey, "

        try:
            self.prefs.hotkey_enter_mission = values.get('ux_hotkey_enter_mission')
        except:
            errors = errors + "'Load Mission' hotkey, "

        try:
            self.prefs.hotkey_dgft_cycle = values.get('ux_hotkey_dgft_cycle')
        except:
            errors = errors + "'DGFT Cycle' hotkey, "

        self.prefs.is_auto_upd_check = values.get('ux_is_auto_upd_check')
        self.prefs.is_tesseract_debug = values.get('ux_is_tesseract_debug')
        self.prefs.is_av_setup_for_unk = values.get('ux_av_setup_unknown')
        self.prefs.is_f10_elev_clamped = values.get('ux_is_f10_elev_clamped')
        self.prefs.is_load_auto_quit = values.get('ux_is_load_auto_quit')
        self.prefs.is_disable_export = values.get('ux_is_disable_export')

        self.prefs.persist_prefs()

        return errors[:-2] if len(errors) > 0 else None

    # build the ui for the preferences window.
    #
    def create_gui(self):
        is_auto_upd_check = self.prefs.is_auto_upd_check_bool
        is_tesseract_debug = self.prefs.is_tesseract_debug_bool
        is_av_setup_for_unk = self.prefs.is_av_setup_for_unk_bool
        is_f10_elev_clamped = self.prefs.is_f10_elev_clamped_bool
        is_load_auto_quit = self.prefs.is_load_auto_quit_bool
        is_disable_export = self.prefs.is_disable_export_bool
        dcs_bios_ver = dcs_bios_vers_install(self.prefs.path_dcs)
        try:
            as_tmplts = [ "DCS Default" ] + AvionicsSetupModel.list_all_names()
        except:
            as_tmplts = [ "DCS Default" ]

        if self.prefs.av_setup_default not in as_tmplts:
            self.prefs.av_setup_default = "DCS Default"


        layout_paths = [
            [PyGUI.Text("DCS saved games directory:", (26,1), justification="right"),
             PyGUI.Input(self.prefs.path_dcs, key='ux_path_dcs', enable_events=True),
             PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FOLDER,
                          target='ux_path_dcs')],

            [PyGUI.Text("Tesseract executable:", (26,1), justification="right"),
             PyGUI.Input(self.prefs.path_tesseract, key='ux_path_tesseract', enable_events=True),
             PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FILE,
                          target='ux_path_tesseract')],
 
            [PyGUI.Text("Mission file:", (26,1), justification="right"),
             PyGUI.Input(self.prefs.path_mission, key='ux_path_mission', enable_events=True),
             PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FILE,
                          target='ux_path_mission')],
        ]

        layout_hotkeys = [
            [PyGUI.Text("DCS F10 map capture:", (26,1), justification="right"),
             PyGUI.Input(self.prefs.hotkey_capture, key='ux_hotkey_capture', enable_events=True,
                         pad=((5,80),0))],

            [PyGUI.Text("Toggle capture mode:", (26,1), justification="right"),
             PyGUI.Input(self.prefs.hotkey_capture_mode, key='ux_hotkey_capture_mode',
                         enable_events=True)],

            [PyGUI.Text("", font="Helvetica 6", pad=(0,0))],

            [PyGUI.Text("Load current profile into jet:", (26,1), justification="right"),
             PyGUI.Input(self.prefs.hotkey_enter_profile, key='ux_hotkey_enter_profile',
                         enable_events=True)],

            [PyGUI.Text("Load mission file into jet:", (26,1), justification="right"),
             PyGUI.Input(self.prefs.hotkey_enter_mission, key='ux_hotkey_enter_mission',
                         enable_events=True)],

            [PyGUI.Text("Quit after hot key load finishes:", (26,1), justification="right"),
             PyGUI.Checkbox("", default=is_load_auto_quit, key='ux_is_load_auto_quit'),
             PyGUI.Text("(applies to cockpit buttons mapped as hot keys)", pad=((0,14),0))],

            [PyGUI.Text("", font="Helvetica 6", pad=(0,0))],

            [PyGUI.Text("F-16 HOTAS DGFT cycle keybind:", (26,1), justification="right"),
             PyGUI.Input(self.prefs.hotkey_dgft_cycle, key='ux_hotkey_dgft_cycle',
                         enable_events=True)],
        ]

        layout_dcsbios = [
            [PyGUI.Text("Button press (short):", (26,1), justification="right"),
             PyGUI.Input(self.prefs.dcs_btn_rel_delay_short, key='ux_dcs_btn_rel_delay_short',
                         enable_events=True),
             PyGUI.Text("(seconds)", justification="left", pad=((0,14),0))],

            [PyGUI.Text("Button press (medium):", (26,1), justification="right"),
             PyGUI.Input(self.prefs.dcs_btn_rel_delay_medium, key='ux_dcs_btn_rel_delay_medium',
                         enable_events=True),
             PyGUI.Text("(seconds)", justification="left", pad=((0,14),0))],

            [PyGUI.Text("Disable export stream parser:", (26,1), justification="right"),
             PyGUI.Checkbox("", default=is_disable_export, key='ux_is_disable_export'),
             PyGUI.Text("(restart DCSWE to apply changes)", pad=((0,14),0))],

            [PyGUI.Text("DCS-BIOS:", (26,1), justification="right"),
             PyGUI.Text("Status", key='ux_dcs_bios_stat', size=(19,1)),
             PyGUI.Button("Install", key='ux_install', size=(18,1),
                          disabled=(dcs_bios_ver is not None))]
        ]

        layout_misc = [
            [PyGUI.Text("Default airframe:", (26,1), justification="right"),
             PyGUI.Combo(values=airframe_list(),
                         default_value=airframe_type_to_ui_text(self.prefs.airframe_default),
                         key='ux_airframe_default', readonly=True, enable_events=True,
                         size=(27,1), pad=((5,194),0))],

            [PyGUI.Text("Default avionics setup:", (26,1), key='ux_av_setup_txt',
                        justification="right"),
             PyGUI.Combo(values=as_tmplts, default_value=self.prefs.av_setup_default,
                         key='ux_av_setup_default', readonly=True, enable_events=True,
                         size=(27,1), pad=((6,2),8)),
             PyGUI.Checkbox("Use when setup unknown", default=is_av_setup_for_unk,
                            key='ux_av_setup_unknown', pad=((6,8),6))],

            [PyGUI.Text("DCS F10 clamps elevation:", (26,1), justification="right", pad=(6,(6,0))),
             PyGUI.Checkbox("", default=is_f10_elev_clamped, key='ux_is_f10_elev_clamped', pad=(0,(6,0)))],

            [PyGUI.Text("DCS F10 logs OCR output:", (26,1), justification="right", pad=(6,(0,6))),
             PyGUI.Checkbox("", default=is_tesseract_debug, key='ux_is_tesseract_debug', pad=(0,(0,6)))],

            [PyGUI.Text("Check for updates:", (26,1), justification="right", pad=(6,6)),
             PyGUI.Checkbox("", default=is_auto_upd_check, key='ux_is_auto_upd_check', pad=(0,6))]
        ]

        return PyGUI.Window("Preferences",
                            [[PyGUI.Frame("Paths & Files", layout_paths)],
                             [PyGUI.Frame("DCS/DCSWE Interaction Hot Keys", layout_hotkeys)],
                             [PyGUI.Frame("DCS BIOS Parameters", layout_dcsbios)],
                             [PyGUI.Frame("Miscellaneous", layout_misc)],
                             [PyGUI.Button("OK", key='ux_ok', size=(8,1), pad=((288,0),16))]],
                            modal=True, finalize=True)

    # update gui for changes to the dcs path
    #
    def update_gui_for_dcs_path(self):
        db_ver = dcs_bios_vers_install(self.prefs.path_dcs)
        if db_ver is None:
            db_ver_latest = dcs_bios_vers_latest()
            self.window['ux_dcs_bios_stat'].update(value="Not Detected")
            self.window['ux_install'].update(text=f"Install v{db_ver_latest}", disabled=False)
        else:
            self.window['ux_dcs_bios_stat'].update(value=f"Version {db_ver} Installed")
            if dcs_bios_is_current(self.prefs.path_dcs):
                self.window['ux_install'].update(text=f"Install v{dcs_bios_vers_latest()}",
                                                 disabled=True)
            else:
                self.window['ux_install'].update(text=f"Update to v{dcs_bios_vers_latest()}",
                                                 disabled=False)

    # update gui for changes to the default airframe or avionics setup
    #
    def update_gui_for_airframe_avsetup(self):
        if airframe_ui_text_to_type(self.values['ux_airframe_default']) == "viper":
            self.window['ux_av_setup_default'].update(disabled=False, readonly=True)
            self.window['ux_av_setup_txt'].update(text_color="#ffffff")
            if self.values['ux_av_setup_default'] == "DCS Default":
                self.window['ux_av_setup_unknown'].update(visible=False)
            else:
                self.window['ux_av_setup_unknown'].update(visible=True,
                                                          value=self.prefs.is_av_setup_for_unk_bool)
        else:
            self.window['ux_av_setup_default'].update(value="DCS Default", disabled=True)
            self.window['ux_av_setup_txt'].update(text_color="#b8b8b8")
            self.window['ux_av_setup_unknown'].update(visible=False)

    def validate_none(self, value, quiet=False):
        return

    def validate_dcs_path(self, value, quiet=False):
        if os.path.exists(value):
            self.prefs_persist(self.values)
            self.update_gui_for_dcs_path()
        elif not quiet:
            PyGUI.Popup("A valid path to the saved games tree for your DCS installation is" +
                        " required. Some functionality may be unavailable if the path is invalid.",
                        title="Invalid DCS Path")

    def validate_tesseract_path(self, value, quiet=False):
        if os.path.exists(value):
            self.prefs_persist(self.values)
        elif not quiet:
            PyGUI.Popup("A valid path to Tesseract is required. Some functionality may be" +
                        " unavailable if the path is invalid.",
                        title="Invalid Tesseract Path")
    
    def core_validate_hot_key(self, value, key, quiet=False):
        if self.prefs.is_hotkey_valid(value):
            self.prefs_persist(self.values)
        elif not quiet:
            PyGUI.Popup(f"The '{key}' hotkey specification is invalid.", title="Invalid Hotkey")

    def validate_capture_hot_key(self, value, quiet=False):
        self.core_validate_hot_key(value, "F10 Capture", quiet)

    def validate_capture_mode_hot_key(self, value, quiet=False):
        self.core_validate_hot_key(value, "F10 Capture Mode", quiet)

    def validate_enter_profile_hot_key(self, value, quiet=False):
        self.core_validate_hot_key(value, "Load Current Profile", quiet)

    def validate_enter_mission_hot_key(self, value, quiet=False):
        self.core_validate_hot_key(value, "Load Mission", quiet)

    def validate_dog_dog_hot_key(self, value, quiet=False):
        self.core_validate_hot_key(value, "DGFT Dogfight", quiet)

    def validate_dog_center_hot_key(self, value, quiet=False):
        self.core_validate_hot_key(value, "DGFT Center", quiet)

    def core_validate_duration(self, value, type, quiet=False):
        try:
            if float(value) <= 0.0:
                raise Exception("Invalid value")
            self.prefs_persist(self.values)
        except:
            if not quiet:
                PyGUI.Popup(f"The {type} button press duration is invalid.", title="Invalid Duration")

    def validate_rds_duration(self, value, quiet=False):
        self.core_validate_duration(value, "short", quiet)

    def validate_rdm_duration(self, value, quiet=False):
        self.core_validate_duration(value, "medium", quiet)

    # run the gui for the preferences window.
    #
    def run(self):
        is_accepted = True

        event, self.values = self.window.read(timeout=0)

        self.update_gui_for_dcs_path()
        self.update_gui_for_airframe_avsetup()

        edit_text_val_map = { 'ux_path_dcs' : self.validate_dcs_path,
                              'ux_path_tesseract' : self.validate_tesseract_path,
                              'ux_path_mission' : self.validate_none,
                              'ux_hotkey_capture' : self.validate_capture_hot_key,
                              'ux_hotkey_capture_mode' : self.validate_capture_mode_hot_key,
                              'ux_hotkey_enter_profile' : self.validate_enter_profile_hot_key,
                              'ux_hotkey_enter_mission' : self.validate_enter_mission_hot_key,
                              'ux_hotkey_dgft_dogfight' : self.validate_dog_dog_hot_key,
                              'ux_hotkey_dgft_center' : self.validate_dog_center_hot_key,
                              'ux_dcs_btn_rel_delay_short' : self.validate_rds_duration,
                              'ux_dcs_btn_rel_delay_medium' : self.validate_rdm_duration
        }

        while True:
            new_event, new_values = self.window.Read()
            self.logger.debug(f"Prefs Event: {event}")
            self.logger.debug(f"Prefs Values: {self.values}")
            if new_values is not None:
                self.values = new_values

            self.logger.debug(f"{event} / {new_event}")
            if event != new_event and event in edit_text_val_map.keys():
                if event == 'ux_ok' or event is None:
                    (edit_text_val_map[event])(self.values[event], quiet=True)
                else:
                    (edit_text_val_map[event])(self.values[event], quiet=False)
            event = new_event

            if event == 'ux_ok' or event is None:
                errors = self.prefs_persist(self.values)
                if errors is not None:
                    if errors.count(',') >= 2:
                        msg_inval = f"Invalid values for {errors}"
                        msg_action = f"Changes to these preferences will be ignored."
                        title = "Invalid Preferences"
                    else:
                        msg_inval = f"Invalid value for {errors}"
                        msg_action = f"Changes to this preference will be ignored."
                        title = "Invalid Preference"
                    if event == 'ux_ok' and \
                       PyGUI.PopupOKCancel(f"{msg_inval}. Are you sure you want to close the window?",
                                           title=title) == "Cancel":
                        continue
                    elif event != 'ux_ok':
                        PyGUI.Popup(f"{msg_inval}. {msg_action}", title=title)
                if not dcs_bios_vers_install(self.prefs.path_dcs):
                    PyGUI.Popup("DCS-BIOS not detected. Some functionality may not be available.",
                                title="Note")
                break

            elif event == 'ux_install':
                self.prefs_persist(self.values)
                try:
                    self.logger.info("Installing DCS BIOS...")
                    if dcs_bios_install(self.prefs.path_dcs) is None:
                        PyGUI.Popup(f"DCS-BIOS failed to install.", title="Error")
                except (FileExistsError, FileNotFoundError, requests.HTTPError) as e:
                    self.logger.error("DCS-BIOS failed to install", exc_info=True)
                    PyGUI.Popup(f"DCS-BIOS failed to install:\n{e}", title="Error")
                self.update_gui_for_dcs_path()
    
            elif event == 'ux_path_dcs':
                self.prefs_persist(self.values)
                self.update_gui_for_dcs_path()
            
            elif event == 'ux_airframe_default' or event == 'ux_av_setup_default':
                self.update_gui_for_airframe_avsetup()

        self.close()
        
        return is_accepted

    def close(self):
        self.window.Close()
