'''
*
*  avionics_setup.py: DCS Waypoint Editor Avionics Setup template editor GUI 
*
*  Copyright (C) 2021 twillis/ilominar
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

import copy
import PySimpleGUI as PyGUI

from src.db_models import AvionicsSetupModel
from src.gui_util import airframe_type_to_ui_text
from src.logger import get_logger


# Maps UI text : MFD OSB button (from format selection screen) for MFD formats.
#
mfd_format_map = { ""     : 1,
                   "DTE"  : 8,
                   "FCR"  : 20,
                   "FLCS" : 10,
                   "HAD"  : 2,
                   "HSD"  : 7,
                   "SMS"  : 6,
                   "TEST" : 9,
                   "TGP"  : 19,
                   "WPN"  : 18
}

# Maps UI MFD format key base onto default MFD format setups (as of DCS v2.8.0.32235).
#
mfd_default_setup_map = { 'ux_nav' : [ 20, 9, 8, 6, 7, 1 ],     # L: FCR, TEST, DTE; R: SMS, HSD, -
                          'ux_air' : [ 20, 10, 9, 6, 7, 1 ],    # L: FCR, FLCS, TEST; R: SMS, HSD -
                          'ux_gnd' : [ 20, 10, 9, 6, 7, 1 ],    # L: FCR, FLCS, TEST; R: SMS, HSD -
                          'ux_dog' : [ 20, 1, 1, 6, 1, 1 ]      # L: FCR, -, -; R: SMS, -, -
}

# Maps UI JHMCS declutter levels onto dbase value.
#
jhmcs_dc_setup_map = { "Level 1 (Show All Content)" : 0,
                       "Level 2 (Hide Heading, Waypoint, Altitude)" : 1,
                       "Level 3 (Show Mode Only)" : 2
}

# Suffixes for MFD format selection combo boxes in the UI. These appear in the order the
# corresponding formats appear on the MFDs when reading from left to right.
#
mfd_key_suffixes = [ '_l14', '_l13', '_l12', '_r14', '_r13', '_r12' ]

# CMDS types and parameters.
#
cmds_types = [ 'c', 'f' ]
cmds_params = [ 'bq', 'bi', 'sq', 'si' ]

# CMDS program defaults.
#
# These are "<chaff> ; <flare>", where <chaff> or <flare> is "<BQ>,<BI>,<SQ>,<SI>"
#
cmds_prog_default_map = { 'MAN 1'  : "1,0.020,10,1.00;1,0.020,10,1.00",
                          'MAN 2'  : "1,0.020,10,0.50;1,0.020,10,0.50",
                          'MAN 3'  : "2,0.100,5,1.00;2,0.100,5,1.00",
                          'MAN 4'  : "2,0.100,5,0.50;2,0.100,5,0.50",
                          'Panic'  : "2,0.050,20,0.75;2,0.050,20,0.75",
                          'Bypass' : "1,0.020,1,0.50;1,0.020,1,0.50"
}

class AvionicsSetupGUI:

    def __init__(self, airframe=None, cur_av_setup=None):
        self.logger = get_logger(__name__)
        self.dbase_setup = None
        self.values = None
        self.cur_cmds_prog_sel = "MAN 1"
        self.cur_cmds_prog_map = { }
        self.cur_av_setup = cur_av_setup

        self.window = self.create_gui(airframe)

        if self.cur_av_setup is not None:
            try:
                self.dbase_setup = AvionicsSetupModel.get(AvionicsSetupModel.name == self.cur_av_setup)
            except:
                self.cur_av_setup = "DCS Default"
        else:
            self.cur_av_setup = "DCS Default"

        self.is_dirty = False

    def is_setup_default(self):
        if self.values.get('ux_tmplt_select') == "DCS Default":
            return True
        return False

    def create_gui(self, airframe="viper"):
        mfd_formats = list(mfd_format_map.keys())
        airframe_ui = airframe_type_to_ui_text(airframe)

        # ---- MFD Formats

        layout_nav = [
            [PyGUI.Checkbox("Reconfigure MFD formats:", key='ux_nav_ckbx', enable_events=True,
                            size=(19,1)),
             PyGUI.Combo(values=mfd_formats, default_value="FCR", key='ux_nav_l14',
                         enable_events=True, size=(8,1), pad=((0,6),0)),
             PyGUI.Combo(values=mfd_formats, default_value="TEST", key='ux_nav_l13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="DTE", key='ux_nav_l12',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.VerticalSeparator(pad=(12,0)),
             PyGUI.Combo(values=mfd_formats, default_value="SMS", key='ux_nav_r14',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="HSD", key='ux_nav_r13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_nav_r12',
                         enable_events=True, size=(8,1), pad=(6,0))],

            [PyGUI.Text("L OSB 14", key='ux_nav_txt_l14', size=(8,1), pad=((200,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 13", key='ux_nav_txt_l13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 12", key='ux_nav_txt_l12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 14", key='ux_nav_txt_r14', size=(8,1), pad=((58,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 13", key='ux_nav_txt_r13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 12", key='ux_nav_txt_r12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8")]
        ]

        layout_air = [
            [PyGUI.Checkbox("Reconfigure MFD formats:", key='ux_air_ckbx', enable_events=True,
                            size=(19,1)),
             PyGUI.Combo(values=mfd_formats, default_value="FCR", key='ux_air_l14',
                         enable_events=True, size=(8,1), pad=((0,6),0)),
             PyGUI.Combo(values=mfd_formats, default_value="FLCS", key='ux_air_l13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="TEST", key='ux_air_l12',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.VerticalSeparator(pad=(12,0)),
             PyGUI.Combo(values=mfd_formats, default_value="SMS", key='ux_air_r14',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="HSD", key='ux_air_r13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_air_r12',
                         enable_events=True, size=(8,1), pad=(6,0))],

            [PyGUI.Text("L OSB 14", key='ux_air_txt_l14', size=(8,1), pad=((200,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 13", key='ux_air_txt_l13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 12", key='ux_air_txt_l12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 14", key='ux_air_txt_r14', size=(8,1), pad=((58,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 13", key='ux_air_txt_r13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 12", key='ux_air_txt_r12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8")]
        ]

        layout_gnd = [
            [PyGUI.Checkbox("Reconfigure MFD formats:", key='ux_gnd_ckbx', enable_events=True,
                            size=(19,1)),
             PyGUI.Combo(values=mfd_formats, default_value="FCR", key='ux_gnd_l14',
                         enable_events=True, size=(8,1), pad=((0,6),0)),
             PyGUI.Combo(values=mfd_formats, default_value="FLCS", key='ux_gnd_l13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="TEST", key='ux_gnd_l12',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.VerticalSeparator(pad=(12,0)),
             PyGUI.Combo(values=mfd_formats, default_value="SMS", key='ux_gnd_r14',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="HSD", key='ux_gnd_r13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_gnd_r12',
                         enable_events=True, size=(8,1), pad=(6,0))],

            [PyGUI.Text("L OSB 14", key='ux_gnd_txt_l14', size=(8,1), pad=((200,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 13", key='ux_gnd_txt_l13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 12", key='ux_gnd_txt_l12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 14", key='ux_gnd_txt_r14', size=(8,1), pad=((58,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 13", key='ux_gnd_txt_r13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 12", key='ux_gnd_txt_r12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8")]
        ]

        layout_dog = [
            [PyGUI.Checkbox("Reconfigure MFD formats:", key='ux_dog_ckbx', enable_events=True,
                            size=(19,1)),
             PyGUI.Combo(values=mfd_formats, default_value="FCR", key='ux_dog_l14',
                         enable_events=True, size=(8,1), pad=((0,6),0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_dog_l13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_dog_l12',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.VerticalSeparator(pad=(12,0)),
             PyGUI.Combo(values=mfd_formats, default_value="SMS", key='ux_dog_r14',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_dog_r13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_dog_r12',
                         enable_events=True, size=(8,1), pad=(6,0))],

            [PyGUI.Text("L OSB 14", key='ux_dog_txt_l14', size=(8,1), pad=((200,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 13", key='ux_dog_txt_l13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 12", key='ux_dog_txt_l12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 14", key='ux_dog_txt_r14', size=(8,1), pad=((58,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 13", key='ux_dog_txt_r13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 12", key='ux_dog_txt_r12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8")]
        ]

        layout_mfd_tab = [
            PyGUI.Tab("MFD Formats",
                      [[PyGUI.Frame("Navigation Master Mode", layout_nav, pad=(12,(12,6)))],
                       [PyGUI.Frame("Air-to-Ground Master Mode (ICP AG)", layout_gnd, pad=(12,6))],
                       [PyGUI.Frame("Air-to-Air Master Mode (ICP AA)," +
                                    " Dogfight MSL Override Mode (DGFT MSL OVRD)",
                                    layout_air, pad=(12,6))],
                       [PyGUI.Frame("Dogfight Override Mode (DGFT DOGFIGHT)",
                                    layout_dog, pad=(12,(6,12)))],
                       [PyGUI.Checkbox("Only set MFD formats when they differ from the default format assignments (reduces setup time)",
                                       key='ux_mfd_force', enable_events=True, size=(72,1), pad=(10,(0,12)))]])
        ]

        # ---- TACAN

        layout_tacan = [
            [PyGUI.Checkbox("Setup TACAN yardstick at:", key='ux_tacan_ckbx', enable_events=True,
                            size=(19,1), pad=(6,(6,8))),
             PyGUI.Input(default_text="1", key='ux_tacan_chan', enable_events=True,
                         size=(4,1), pad=(6,(6,8))),
             PyGUI.Combo(values=[ "X", "Y" ], default_value="X", key='ux_tacan_xy_select',
                         readonly=True, enable_events=True, size=(2,1), pad=(6,(6,8))),
             PyGUI.Text("for role", key='ux_tacan_role', pad=(6,(6,8))),
             PyGUI.Combo(values=[ "Flight Lead", "Wingman" ], default_value="Flight Lead",
                         key='ux_tacan_lw_select', enable_events=True, readonly=True,
                         size=(10,1), pad=(6,(6,8))),
             PyGUI.Text("", key='ux_tacan_info',
                        size=(34,1), pad=(6,(6,8)))]
        ]

        layout_tacan_tab = [
            PyGUI.Tab("TACAN", [[PyGUI.Frame("Yardstick", layout_tacan, pad=(12,12))]])
        ]

        # ---- CMDS

        layout_cmds_sel = [
            PyGUI.Text("Program:", pad=((12,4),(12,6))),
            PyGUI.Combo(values=["MAN 1", "MAN 2", "MAN 3", "MAN 4", "Panic", "Bypass"],
                        default_value=self.cur_cmds_prog_sel, key='ux_cmds_prog_sel',
                        readonly=True, enable_events=True, size=(8,1), pad=(6,(12,6))),
            PyGUI.Checkbox("Change this program from aircraft defaults", key='ux_cmds_reconfig',
                           enable_events=True, pad=(6,(12,6)))
        ]

        layout_cmds_prog_params = [
            PyGUI.Frame("Chaff",
                        [[PyGUI.Text("Burst Quantity:", key='ux_cmds_c_bq_t1',
                                     justification="right", size=(12,1), pad=(8,4)),
                          PyGUI.Input(default_text="", key='ux_cmds_c_bq', enable_events=True,
                                      size=(6,1), pad=((0,6),4)),
                          PyGUI.Text("(chaff)", key='ux_cmds_c_bq_t2', pad=((0,8),(6,4)))],

                        [PyGUI.Text("Burst Interval:", key='ux_cmds_c_bi_t1',
                                    justification="right", size=(12,1), pad=(8,4)),
                         PyGUI.Input(default_text="", key='ux_cmds_c_bi', enable_events=True,
                                     size=(6,1), pad=((0,6),4)),
                         PyGUI.Text("(seconds)", key='ux_cmds_c_bi_t2', pad=((0,8),4))],

                        [PyGUI.Text("Salvo Quantity:", key='ux_cmds_c_sq_t1',
                                    justification="right", size=(12,1), pad=(8,4)),
                         PyGUI.Input(default_text="", key='ux_cmds_c_sq', enable_events=True,
                                     size=(6,1), pad=((0,6),4)),
                         PyGUI.Text("(bursts)", key='ux_cmds_c_sq_t2', pad=((0,8),4))],

                        [PyGUI.Text("Salvo Interval:", key='ux_cmds_c_si_t1',
                                    justification="right", size=(12,1), pad=(8,4)),
                         PyGUI.Input(default_text="", key='ux_cmds_c_si', enable_events=True,
                                     size=(6,1), pad=((0,6),4)),
                         PyGUI.Text("(seconds)", key='ux_cmds_c_si_t2', pad=((0,8),(4,8)))]], pad=(12,6)),
            PyGUI.Frame("Flare",
                        [[PyGUI.Text("Burst Quantity:", key='ux_cmds_f_bq_t1',
                                     justification="right", size=(12,1), pad=(8,4)),
                          PyGUI.Input(default_text="", key='ux_cmds_f_bq', enable_events=True,
                                      size=(6,1), pad=((0,6),4)),
                          PyGUI.Text("(flare)", key='ux_cmds_f_bq_t2', pad=((0,8),(6,4)))],

                        [PyGUI.Text("Burst Interval:", key='ux_cmds_f_bi_t1',
                                    justification="right", size=(12,1), pad=(8,4)),
                         PyGUI.Input(default_text="", key='ux_cmds_f_bi', enable_events=True,
                                     size=(6,1), pad=((0,6),4)),
                         PyGUI.Text("(seconds)", key='ux_cmds_f_bi_t2', pad=((0,8),4))],

                        [PyGUI.Text("Salvo Quantity:", key='ux_cmds_f_sq_t1',
                                    justification="right", size=(12,1), pad=(8,4)),
                         PyGUI.Input(default_text="", key='ux_cmds_f_sq', enable_events=True,
                                     size=(6,1), pad=((0,6),4)),
                         PyGUI.Text("(bursts)", key='ux_cmds_f_sq_t2', pad=((0,8),4))],

                        [PyGUI.Text("Salvo Interval:", key='ux_cmds_f_si_t1',
                                    justification="right", size=(12,1), pad=(8,4)),
                         PyGUI.Input(default_text="", key='ux_cmds_f_si', enable_events=True,
                                     size=(6,1), pad=((0,6),4)),
                         PyGUI.Text("(seconds)", key='ux_cmds_f_si_t2', pad=((0,8),(4,8)))]], pad=(12,6))
        ]

        layout_cmds_prog_updates = [
            PyGUI.Text("Programs to be updated:", pad=((12,4),6)),
            PyGUI.Text("None", key='ux_cmds_prog_update', pad=((4,6),6), size=(30,1))
        ]

        layout_cmds_tab = [
            PyGUI.Tab("CMDS",
                      [layout_cmds_sel, layout_cmds_prog_params, layout_cmds_prog_updates])
        ]

        # ---- Miscellaneous

        layout_bulls = [
            PyGUI.Frame("Bullseye",
                        [[PyGUI.Text("FCR and HSD MFD formats display:"),
                          PyGUI.Combo(values=[ "Steering Cue", "Ownship Bullseye" ], default_value="Steering Cue",
                                      key='ux_bulls_select', enable_events=True, readonly=True,
                                      size=(18,1), pad=(6,(6,8))),
                          PyGUI.Text("", size=(40,1), pad=((6,7),6))]], pad=(12,6))
        ]

        layout_jhmcs = [
            PyGUI.Frame("JHMCS",
                        [[PyGUI.Checkbox("Blank HMCS when looking through HUD", key='ux_jhmcs_hud',
                           enable_events=True, pad=(6,(6,6)))],
                         [PyGUI.Checkbox("Blank HMCS when looking in cockpit", key='ux_jhmcs_pit',
                           enable_events=True, pad=(6,(6,6)))],
                         [PyGUI.Checkbox("HMCS displays RWR information", key='ux_jhmcs_rwr',
                          enable_events=True, pad=(6,(6,6)))],
                         [PyGUI.Text("HMCS declutter:"),
                          PyGUI.Combo(values=[ "Level 1 (Show All Content)",
                                               "Level 2 (Hide Heading, Waypoint, Altitude)",
                                               "Level 3 (Show Mode Only)" ],
                                      default_value="Level 1 (Show All Content)",
                                      key='ux_jhmcs_dc_select', enable_events=True, readonly=True,
                                      size=(38,1), pad=(6,(6,8))),
                          PyGUI.Text("", size=(37,1), pad=((6,7),6))]], pad=(12,6))
        ]
        
        layout_misc_tab = [
            PyGUI.Tab("Miscellaneous",
                      [layout_bulls, layout_jhmcs])
        ]

        # ---- Management Controls

        layout_mgmt = [
            [PyGUI.Text("Avionics setup:"),
             PyGUI.Combo(values=["DCS Default"], key='ux_tmplt_select', readonly=True,
                         enable_events=True, size=(29,1)),
             PyGUI.Button("Save As...", key='ux_tmplt_save_as', size=(10,1)),
             PyGUI.Button("Update", key='ux_tmplt_update', size=(10,1)),
             PyGUI.Button("Delete...", key='ux_tmplt_delete', size=(10,1)),
             PyGUI.VerticalSeparator(pad=(16,12)),
             PyGUI.Button("Done", key='ux_done', size=(10,1), pad=(6,12))]
        ]

        return PyGUI.Window(f"{airframe_ui} Avionics Setup",
                            [[PyGUI.TabGroup([layout_mfd_tab,
                                              layout_tacan_tab,
                                              layout_cmds_tab,
                                              layout_misc_tab], pad=(8,8))],
                             [layout_mgmt]],
                            enable_close_attempted_event=True, modal=True, finalize=True)

    # update the gui for the enable state of a MFD master mode
    #
    def update_gui_enable_mfd_row(self, key_base):
        if self.values[f"{key_base}_ckbx"]:
            label_color = "#ffffff"
            for key_suffix in mfd_key_suffixes:
                self.window[f"{key_base}{key_suffix}"].update(disabled=False)
        else:
            label_color = "#b8b8b8"
            self.window[f"{key_base}_l14"].update(value="FCR", disabled=True)
            if key_base == 'ux_nav':
                self.window[f"{key_base}_l13"].update(value="TEST", disabled=True)
                self.window[f"{key_base}_l12"].update(value="DTE", disabled=True)
            elif key_base == 'ux_gnd' or key_base == 'ux_air':
                self.window[f"{key_base}_l13"].update(value="FLCS", disabled=True)
                self.window[f"{key_base}_l12"].update(value="TEST", disabled=True)
            else:
                self.window[f"{key_base}_l13"].update(value="", disabled=True)
                self.window[f"{key_base}_l12"].update(value="", disabled=True)
            self.window[f"{key_base}_r14"].update(value="SMS", disabled=True)
            if key_base == 'ux_dog':
                self.window[f"{key_base}_r13"].update(value="", disabled=True)
            else:
                self.window[f"{key_base}_r13"].update(value="HSD", disabled=True)
            self.window[f"{key_base}_r12"].update(value="", disabled=True)
        for key_suffix in mfd_key_suffixes:
            self.window[f"{key_base}_txt{key_suffix}"].update(text_color=label_color)

    # update the gui to ensure a format appears only once in a master mode
    #
    def update_gui_unique_mfd_row(self, key, key_base):
        value = self.values[key]
        for key_suffix in mfd_key_suffixes:
            row_key = f"{key_base}{key_suffix}"
            if row_key != key and self.values[row_key] == value:
                self.window[row_key].update(value="")

    # update the gui for the enable state of the tacan
    #
    def update_gui_enable_tacan_row(self):
        if self.values['ux_tacan_ckbx']:
            label_color = "#ffffff"
            input_color = "#000000"
            chan = self.values['ux_tacan_chan']
            if self.values['ux_tacan_lw_select'] == "Wingman":
                chan = int(chan) + 63
            xy = self.values['ux_tacan_xy_select']
            summary_txt = f" (setup will program TACAN to {chan}{xy} A/A)"
            self.window['ux_tacan_chan'].update(disabled=False, text_color=input_color)
            self.window['ux_tacan_xy_select'].update(disabled=False, readonly=True)
            self.window['ux_tacan_lw_select'].update(disabled=False, readonly=True)
        else:
            label_color = "#b8b8b8"
            input_color = "#b8b8b8"
            summary_txt = ""
            self.window['ux_tacan_chan'].update(disabled=True, text_color=input_color)
            self.window['ux_tacan_xy_select'].update(disabled=True)
            self.window['ux_tacan_lw_select'].update(disabled=True)
        self.window['ux_tacan_role'].update(text_color=label_color)
        self.window['ux_tacan_info'].update(summary_txt)

    # update the gui for the enable state of the cmds
    #
    def update_gui_enable_cmds(self):
        if self.values['ux_cmds_reconfig']:
            label_color = "#ffffff"
            input_color = "#000000"
            disabled = False
        else:
            label_color = "#b8b8b8"
            input_color = "#b8b8b8"
            disabled = True
        updating = None
        for cmds_type in cmds_types:
            for cmds_param in cmds_params:
                self.window[f"ux_cmds_{cmds_type}_{cmds_param}"].update(disabled=disabled,
                                                                        text_color=input_color)
                self.window[f"ux_cmds_{cmds_type}_{cmds_param}_t1"].update(text_color=label_color)
                self.window[f"ux_cmds_{cmds_type}_{cmds_param}_t2"].update(text_color=label_color)
        prog_list = "None"
        for prog in [ 'MAN 1', 'MAN 2', 'MAN 3', 'MAN 4', 'Panic', 'Bypass']:
            if self.cur_cmds_prog_map[prog]:
                if prog_list == "None":
                    prog_list = prog
                else:
                    prog_list += f", {prog}"
        self.window['ux_cmds_prog_update'].update(prog_list)

    # update the gui state based on a change to the template list
    #
    def update_gui_template_list(self):
        tmplts = [ "DCS Default" ] + AvionicsSetupModel.list_all_names()
        if self.dbase_setup is None:
            cur_av_setup = "DCS Default"
        else:
            cur_av_setup = self.dbase_setup.name
        self.window['ux_tmplt_select'].update(values=tmplts, set_to_index=tmplts.index(cur_av_setup))
        self.values['ux_tmplt_select'] = cur_av_setup
        self.update_gui_control_enable_state()

    # update the gui button state based on current setup
    #
    def update_gui_control_enable_state(self):
        if self.is_dirty:
            save_disabled = False
        else:
            save_disabled = True
        if self.is_setup_default():
            self.window['ux_tmplt_save_as'].update(disabled=save_disabled)
            self.window['ux_tmplt_update'].update(disabled=True)
            self.window['ux_tmplt_delete'].update(disabled=True)
        else:
            self.window['ux_tmplt_save_as'].update(disabled=save_disabled)
            self.window['ux_tmplt_update'].update(disabled=save_disabled)
            self.window['ux_tmplt_delete'].update(disabled=False)


    # get/set mfd format row ui state
    #
    # the state is expressed in the database format (csv list of osb numbers, see the definition
    # of the f16_mfd_setup_* fields in the database model).
    #
    def get_gui_mfd_row(self, key_base):
        if self.values[f"{key_base}_ckbx"] == False:
            config = None
        else:
            osb_list = []
            for key_suffix in mfd_key_suffixes:
                osb_list.append(mfd_format_map[self.values[f"{key_base}{key_suffix}"]])
            config = ','.join([str(item) for item in osb_list])
        return config
    
    def set_gui_mfd_row(self, key_base, value):
        if value is None:
            self.window[f"{key_base}_ckbx"].update(value=False)
            osb_list = copy.copy(mfd_default_setup_map[key_base])
        else:
            self.window[f"{key_base}_ckbx"].update(value=True)
            osb_list = [ int(osb) for osb in value.split(",") ]
        for key_suffix in mfd_key_suffixes:
            osb = osb_list.pop(0)
            hits = [k for k,v in mfd_format_map.items() if v == osb]
            if (len(hits) == 0):
                hits = [""]
            self.window[f"{key_base}{key_suffix}"].update(value=hits[0])

    # get/set cmds program state
    #
    def get_gui_cmds_prog_field_quant(self, value):
        try:
            value_as_int = int(value)
            if value_as_int < 0 or value_as_int > 99:
                raise ValueError("Out of bounds")
        except:
            value_as_int = 0
        return f"{value_as_int:#d}"

    def get_gui_cmds_prog_field_bint(self, value):
        try:
            value_as_float = float(value)
            if (value_as_float < 0.020 or value_as_float > 10.0):
                raise ValueError("Out of bounds")
        except:
            value_as_float = 0.02
        return f"{value_as_float:#0.3f}"

    def get_gui_cmds_prog_field_sint(self, value, quiet=False):
        try:
            value_as_float = float(value)
            if (value_as_float < 0.50 or value_as_float > 150.0):
                raise ValueError("Out of bounds")
        except:
            value_as_float = 0.5
        return f"{value_as_float:#0.2f}"

    def get_gui_cmds_prog(self):
        cmds_params_val_map = { 'bq' : self.get_gui_cmds_prog_field_quant,
                                'bi' : self.get_gui_cmds_prog_field_bint,
                                'sq' : self.get_gui_cmds_prog_field_quant,
                                'si' : self.get_gui_cmds_prog_field_sint }
        if self.values['ux_cmds_reconfig'] == True:
            value = ""
            sep = ""
            for cmds_type in cmds_types:
                for cmds_param in cmds_params:
                    value += sep
                    field = self.values[f'ux_cmds_{cmds_type}_{cmds_param}']
                    value += cmds_params_val_map[cmds_param](field)
                    sep = ","
                sep = ";"
        else:
            value = None
        return value
    
    def set_gui_cmds_prog(self, value):
        if value is None:
            self.window['ux_cmds_reconfig'].update(value=False)
            self.values['ux_cmds_reconfig'] = False
            for cmds_type in cmds_types:
                for cmds_param in cmds_params:
                    self.window[f"ux_cmds_{cmds_type}_{cmds_param}"].update("")
        else:
            self.window['ux_cmds_reconfig'].update(value=True)
            self.values['ux_cmds_reconfig'] = True
            types = value.split(";")
            c_params = types[0].split(",")
            f_params = types[1].split(",")

            self.window['ux_cmds_c_bq'].update(f"{int(c_params[0]):#d}")
            self.window['ux_cmds_c_bi'].update(f"{float(c_params[1]):#0.3f}")
            self.window['ux_cmds_c_sq'].update(f"{int(c_params[2]):#d}")
            self.window['ux_cmds_c_si'].update(f"{float(c_params[3]):#0.2f}")

            self.window['ux_cmds_f_bq'].update(f"{int(f_params[0]):#d}")
            self.window['ux_cmds_f_bi'].update(f"{float(f_params[1]):#0.3f}")
            self.window['ux_cmds_f_sq'].update(f"{int(f_params[2]):#d}")
            self.window['ux_cmds_f_si'].update(f"{float(f_params[3]):#0.2f}")
        self.update_gui_enable_cmds()
        

    # synchronize TACAN setup UI and database
    #
    def copy_tacan_dbase_to_ui(self):
        if self.dbase_setup is not None:
            if self.dbase_setup.tacan_yard is None:
                self.window['ux_tacan_ckbx'].update(value=False)
                self.window['ux_tacan_chan'].update("1")
            else:
                fields = [ str(field) for field in self.dbase_setup.tacan_yard.split(",") ]
                if fields[2] == "L":
                    role_index = 0
                else:
                    role_index = 1
                self.window['ux_tacan_ckbx'].update(value=True)
                self.window['ux_tacan_chan'].update(fields[0])
                self.window['ux_tacan_xy_select'].update(value=fields[1])
                self.window['ux_tacan_lw_select'].update(set_to_index=role_index)
        else:
            self.window['ux_tacan_ckbx'].update(value=False)
            self.window['ux_tacan_chan'].update("1")
            self.window['ux_tacan_xy_select'].update(value="X")
            self.window['ux_tacan_lw_select'].update(value="Flight Lead")
        self.is_dirty = False

    def copy_tacan_ui_to_dbase(self, db_save=True):
        if self.dbase_setup is not None:
            if self.values['ux_tacan_ckbx'] == False:
                tacan_yard = None
            else:
                chan = int(self.values['ux_tacan_chan'])
                xy = self.values['ux_tacan_xy_select']
                if self.values['ux_tacan_lw_select'] == "Flight Lead":
                    lw = "L"
                else:
                    lw = "W"
                tacan_yard = f"{chan},{xy},{lw}"
            self.dbase_setup.tacan_yard = tacan_yard
            if db_save:
                try:
                    self.dbase_setup.save()
                except:
                    PyGUI.PopupError("Unable to save TACAN yardstick information to database?")
            self.is_dirty = False
    
    # synchronize F-16 MFD setup UI and database
    #
    def copy_f16_mfd_dbase_to_ui(self):
        if self.dbase_setup is not None:
            self.set_gui_mfd_row('ux_nav', self.dbase_setup.f16_mfd_setup_nav)
            self.set_gui_mfd_row('ux_air', self.dbase_setup.f16_mfd_setup_air)
            self.set_gui_mfd_row('ux_gnd', self.dbase_setup.f16_mfd_setup_gnd)
            self.set_gui_mfd_row('ux_dog', self.dbase_setup.f16_mfd_setup_dog)
            self.window['ux_mfd_force'].update(value=self.dbase_setup.f16_mfd_setup_opt)
        else:
            self.set_gui_mfd_row('ux_nav', None)
            self.set_gui_mfd_row('ux_air', None)
            self.set_gui_mfd_row('ux_gnd', None)
            self.set_gui_mfd_row('ux_dog', None)
            self.window['ux_mfd_force'].update(value=False)
        self.is_dirty = False
    
    def copy_f16_mfd_ui_to_dbase(self, db_save=True):
        if self.dbase_setup is not None:
            self.dbase_setup.f16_mfd_setup_nav = self.get_gui_mfd_row('ux_nav')
            self.dbase_setup.f16_mfd_setup_air = self.get_gui_mfd_row('ux_air')
            self.dbase_setup.f16_mfd_setup_gnd = self.get_gui_mfd_row('ux_gnd')
            self.dbase_setup.f16_mfd_setup_dog = self.get_gui_mfd_row('ux_dog')
            self.dbase_setup.f16_mfd_setup_opt = self.values['ux_mfd_force']
            if db_save:
                try:
                    self.dbase_setup.save()
                except:
                    PyGUI.PopupError("Unable to save MFD setup information to database?")
            self.is_dirty = False


    # synchronize F-16 CMDS setup UI and database
    #
    def copy_f16_cmds_dbase_to_ui(self, cur_prog=None):
        if cur_prog is None:
            cur_prog = self.values['ux_cmds_prog_sel']
        if self.dbase_setup is not None:
            self.cur_cmds_prog_map['MAN 1'] = self.dbase_setup.f16_cmds_setup_p1
            self.cur_cmds_prog_map['MAN 2'] = self.dbase_setup.f16_cmds_setup_p2
            self.cur_cmds_prog_map['MAN 3'] = self.dbase_setup.f16_cmds_setup_p3
            self.cur_cmds_prog_map['MAN 4'] = self.dbase_setup.f16_cmds_setup_p4
            self.cur_cmds_prog_map['Panic'] = self.dbase_setup.f16_cmds_setup_p5
            self.cur_cmds_prog_map['Bypass'] = self.dbase_setup.f16_cmds_setup_p6
        else:
            self.cur_cmds_prog_map['MAN 1'] = None
            self.cur_cmds_prog_map['MAN 2'] = None
            self.cur_cmds_prog_map['MAN 3'] = None
            self.cur_cmds_prog_map['MAN 4'] = None
            self.cur_cmds_prog_map['Panic'] = None
            self.cur_cmds_prog_map['Bypass'] = None
        self.set_gui_cmds_prog(self.cur_cmds_prog_map[cur_prog])
        self.is_dirty = False
    
    def copy_f16_cmds_ui_to_dbase(self, cur_prog=None, db_save=True):
        if cur_prog is None:
            cur_prog = self.values['ux_cmds_prog_sel']
        self.cur_cmds_prog_map[cur_prog] = self.get_gui_cmds_prog()
        if self.dbase_setup is not None:
            self.dbase_setup.f16_cmds_setup_p1 = self.cur_cmds_prog_map['MAN 1']
            self.dbase_setup.f16_cmds_setup_p2 = self.cur_cmds_prog_map['MAN 2']
            self.dbase_setup.f16_cmds_setup_p3 = self.cur_cmds_prog_map['MAN 3']
            self.dbase_setup.f16_cmds_setup_p4 = self.cur_cmds_prog_map['MAN 4']
            self.dbase_setup.f16_cmds_setup_p5 = self.cur_cmds_prog_map['Panic']
            self.dbase_setup.f16_cmds_setup_p6 = self.cur_cmds_prog_map['Bypass']
            if db_save:
                try:
                    self.dbase_setup.save()
                except:
                    PyGUI.PopupError("Unable to save CMDS setup information to database?")
            self.copy_f16_cmds_dbase_to_ui()


    # synchronize F-16 Miscellaneous setup UI and database
    #
    def copy_f16_misc_dbase_to_ui(self):
        if self.dbase_setup is not None:
            if self.dbase_setup.f16_bulls_setup is None:
                self.window['ux_bulls_select'].update(set_to_index=0)
            else:
                self.window['ux_bulls_select'].update(set_to_index=self.dbase_setup.f16_bulls_setup)
            if self.dbase_setup.f16_jhmcs_setup is None:
                self.window['ux_jhmcs_hud'].update(value=True)
                self.window['ux_jhmcs_pit'].update(value=True)
                self.window['ux_jhmcs_rwr'].update(value=True)
                self.window['ux_jhmcs_dc_select'].update(set_to_index=0)
            else:
                fields = [ int(field) for field in self.dbase_setup.f16_jhmcs_setup.split(",") ]
                self.window['ux_jhmcs_hud'].update(value=bool(fields[0]))
                self.window['ux_jhmcs_pit'].update(value=bool(fields[1]))
                self.window['ux_jhmcs_rwr'].update(value=bool(fields[2]))
                self.window['ux_jhmcs_dc_select'].update(set_to_index=fields[3])
        else:
            self.window['ux_bulls_select'].update(set_to_index=0)
            self.window['ux_jhmcs_hud'].update(value=True)
            self.window['ux_jhmcs_pit'].update(value=True)
            self.window['ux_jhmcs_rwr'].update(value=True)
            self.window['ux_jhmcs_dc_select'].update(set_to_index=0)
        self.is_dirty = False

    def copy_f16_misc_ui_to_dbase(self, db_save=True):
        if self.dbase_setup is not None:
            if self.values['ux_bulls_select'] == "Ownship Bullseye":
                self.dbase_setup.f16_bulls_setup = "1"
            else:
                self.dbase_setup.f16_bulls_setup = None

            hud = int(self.values['ux_jhmcs_hud'])
            pit = int(self.values['ux_jhmcs_pit'])
            rwr = int(self.values['ux_jhmcs_rwr'])
            dcs = jhmcs_dc_setup_map[self.values['ux_jhmcs_dc_select']]
            jhmcs_setup = f"{hud},{pit},{rwr},{dcs}"
            if jhmcs_setup != "1,1,1,0":
                self.dbase_setup.f16_jhmcs_setup = jhmcs_setup
            else:
                self.dbase_setup.f16_jhmcs_setup = None

            if db_save:
                try:
                    self.dbase_setup.save()
                except:
                    PyGUI.PopupError("Unable to save miscellaneous information to database?")
            self.is_dirty = False


    # gui action handlers
    #
    def do_mfd_osb_ckbx(self, event):
        self.is_dirty = True
        fields = event.split("_")
        self.update_gui_enable_mfd_row(f"{fields[0]}_{fields[1]}")

    def do_mfd_osb_combo(self, event):
        self.is_dirty = True
        fields = event.split("_")
        self.update_gui_unique_mfd_row(event, f"{fields[0]}_{fields[1]}")

    def do_mfd_force(self, event):
        self.is_dirty = True

    def do_tacan_dirty(self, event):
        self.is_dirty = True

    def do_tacan_chan(self, event):
        if self.values[event]:
            try:
                input_as_int = int(self.values[event])
                if input_as_int < 1 or input_as_int > 63:
                    raise ValueError("Out of bounds")
                self.is_dirty = True
            except:
                PyGUI.Popup("The TACAN channel must be between 1 and 63 for use as a yardstick.",
                            title="Invalid Channel")
                self.window[event].update(self.values[event][:-1])

    def do_cmds_reconfig(self, event):
        cur_prog = self.values['ux_cmds_prog_sel']
        if self.values[event] == True:
            program = cmds_prog_default_map[cur_prog]
        else:
            program = None
        self.cur_cmds_prog_map[cur_prog] = program
        self.set_gui_cmds_prog(program)
        self.is_dirty = True
    
    def do_cmds_prog_select(self, event):
        self.cur_cmds_prog_map[self.cur_cmds_prog_sel] = self.get_gui_cmds_prog()
        self.cur_cmds_prog_sel = self.values[event]
        self.set_gui_cmds_prog(self.cur_cmds_prog_map[self.cur_cmds_prog_sel])

    def do_cmds_prog_field_quantity(self, event):
        if self.values[event]:
            if self.val_cmds_prog_field_quantity(self.values[event]):
                self.is_dirty = True
            else:
                self.window[event].update(self.values[event][:-1])

    def do_cmds_prog_field_bint(self, event):
        if self.values[event]:
            if self.val_cmds_prog_field_bint(self.values[event]):
                self.is_dirty = True
            else:
                self.window[event].update(self.values[event][:-1])

    def do_cmds_prog_field_sint(self, event):
        if self.values[event]:
            if self.val_cmds_prog_field_sint(self.values[event]):
                self.is_dirty = True
            else:
                self.window[event].update(self.values[event][:-1])

    def do_misc_dirty(self, event):
        self.is_dirty = True

    def do_template_select(self, event):
        if self.is_dirty:
            action = PyGUI.PopupOKCancel(f"You have unsaved changes to the current template." +
                                         f" Changing the template will discard these changes.",
                                         title="Unsaved Changes")
            if action == "Cancel":
                self.window['ux_tmplt_select'].update(value=self.cur_av_setup)
                return

        if self.is_setup_default():
            self.dbase_setup = None
        else:
            self.dbase_setup = AvionicsSetupModel.get(AvionicsSetupModel.name == self.values[event])
        self.cur_av_setup = self.values['ux_tmplt_select']

        self.cur_cmds_prog_sel = 'MAN 1'
        self.window['ux_cmds_prog_sel'].update(value=self.cur_cmds_prog_sel)

        self.copy_f16_cmds_dbase_to_ui()
        self.copy_f16_mfd_dbase_to_ui()
        self.copy_f16_misc_dbase_to_ui()
        self.copy_tacan_dbase_to_ui()

    def do_template_save_as(self, event):
        name = PyGUI.PopupGetText("Template Name", "Creating New Template")
        if name is not None:
            try:
                self.dbase_setup = AvionicsSetupModel.create(name=name)
                self.copy_f16_cmds_ui_to_dbase(db_save=False)
                self.copy_f16_mfd_ui_to_dbase(db_save=False)
                self.copy_f16_misc_ui_to_dbase(db_save=False)
                self.copy_tacan_ui_to_dbase(db_save=True)
                self.update_gui_template_list()
            except:
                PyGUI.Popup(f"Unable to create a template named '{name}'. Is there already" +
                                " a template with that name?", title="Error")

    def do_template_update(self, event):
        if not self.is_setup_default():
            self.copy_f16_cmds_ui_to_dbase(db_save=True)
            self.copy_f16_mfd_ui_to_dbase(db_save=True)
            self.copy_f16_misc_ui_to_dbase(db_save=True)
            self.copy_tacan_ui_to_dbase(db_save=True)

    def do_template_delete(self, event):
        action = PyGUI.PopupOKCancel(f"Are you sure you want to delete the settings {self.cur_av_setup}?",
                                     title="Confirm Delete")
        if action == "OK":
            try:
                self.dbase_setup.delete_instance()
                self.dbase_setup = None
                self.is_dirty = False
                self.cur_cmds_prog_sel = 'MAN 1'
                self.window['ux_cmds_prog_sel'].update(value=self.cur_cmds_prog_sel)
                self.update_gui_template_list()
                self.copy_f16_cmds_dbase_to_ui()
                self.copy_f16_mfd_dbase_to_ui()
                self.copy_f16_misc_dbase_to_ui()
                self.copy_tacan_dbase_to_ui()
            except Exception as e:
                PyGUI.PopupError(f"Unable to delete the settings {self.cur_av_setup} from the database.")

    def val_cmds_prog_field_quantity(self, value, quiet=False):
        try:
            input_as_int = int(value)
            if input_as_int < 0 or input_as_int > 99:
                raise ValueError("Out of bounds")
            return True
        except:
            if not quiet:
                PyGUI.Popup("The quantity must be between 0 and 99 in a CMDS program.",
                            title="Invalid Quantity")
        return False

    def val_cmds_prog_field_bint(self, value, quiet=False):
        try:
            input_as_float = float(value)
            if (input_as_float < 0.020 or input_as_float > 10.0) and (input_as_float != 0.0):
                raise ValueError("Out of bounds")
            return True
        except:
            if not quiet:
                PyGUI.Popup("The burst interval must be between 0.020 and 10.000 in a CMDS program.",
                            title="Invalid Burst Interval")
        return False

    def val_cmds_prog_field_sint(self, value, quiet=False):
        try:
            input_as_float = float(value)
            if (input_as_float < 0.50 or input_as_float > 150.0) and (input_as_float != 0.0):
                raise ValueError("Out of bounds")
            return True
        except:
            if not quiet:
                PyGUI.Popup("The salvo interval must be between 0.50 and 150.00 in a CMDS program.",
                            title="Invalid Salvo Interval")
        return False

    # run the gui for the preferences window.
    #
    def run(self):
        self.window.disappear()

        try:
            event, self.values = self.window.read(timeout=0)

            self.copy_f16_cmds_dbase_to_ui()
            self.copy_f16_mfd_dbase_to_ui()
            self.copy_f16_misc_dbase_to_ui()
            self.copy_tacan_dbase_to_ui()

            event, self.values = self.window.read(timeout=0)

            self.update_gui_control_enable_state()
            for key_base in ['ux_nav', 'ux_gnd', 'ux_air', 'ux_dog']:
                self.update_gui_enable_mfd_row(key_base)
            self.update_gui_enable_tacan_row()
            self.update_gui_enable_cmds()
            self.update_gui_template_list()

            self.window['ux_tmplt_select'].update(value=self.cur_av_setup)
        except Exception as e:
            self.logger.debug(f"AVS setup fails {e}")

        self.window.reappear()

        handler_map = { 'ux_nav_ckbx' : self.do_mfd_osb_ckbx,
                        'ux_nav_l14' : self.do_mfd_osb_combo,
                        'ux_nav_l13' : self.do_mfd_osb_combo,
                        'ux_nav_l12' : self.do_mfd_osb_combo,
                        'ux_nav_r14' : self.do_mfd_osb_combo,
                        'ux_nav_r13' : self.do_mfd_osb_combo,
                        'ux_nav_r12' : self.do_mfd_osb_combo,
                        'ux_air_ckbx' : self.do_mfd_osb_ckbx,
                        'ux_air_l14' : self.do_mfd_osb_combo,
                        'ux_air_l13' : self.do_mfd_osb_combo,
                        'ux_air_l12' : self.do_mfd_osb_combo,
                        'ux_air_r14' : self.do_mfd_osb_combo,
                        'ux_air_r13' : self.do_mfd_osb_combo,
                        'ux_air_r12' : self.do_mfd_osb_combo,
                        'ux_gnd_ckbx' : self.do_mfd_osb_ckbx,
                        'ux_gnd_l14' : self.do_mfd_osb_combo,
                        'ux_gnd_l13' : self.do_mfd_osb_combo,
                        'ux_gnd_l12' : self.do_mfd_osb_combo,
                        'ux_gnd_r14' : self.do_mfd_osb_combo,
                        'ux_gnd_r13' : self.do_mfd_osb_combo,
                        'ux_gnd_r12' : self.do_mfd_osb_combo,
                        'ux_dog_ckbx' : self.do_mfd_osb_ckbx,
                        'ux_dog_l14' : self.do_mfd_osb_combo,
                        'ux_dog_l13' : self.do_mfd_osb_combo,
                        'ux_dog_l12' : self.do_mfd_osb_combo,
                        'ux_dog_r14' : self.do_mfd_osb_combo,
                        'ux_dog_r13' : self.do_mfd_osb_combo,
                        'ux_dog_r12' : self.do_mfd_osb_combo,
                        'ux_mfd_force' : self.do_mfd_force,
                        'ux_tacan_ckbx' : self.do_tacan_dirty,
                        'ux_tacan_chan' : self.do_tacan_chan,
                        'ux_tacan_xy_select' : self.do_tacan_dirty,
                        'ux_tacan_lw_select' : self.do_tacan_dirty,
                        'ux_cmds_reconfig' : self.do_cmds_reconfig,
                        'ux_cmds_prog_sel' : self.do_cmds_prog_select,
                        'ux_cmds_c_bq' : self.do_cmds_prog_field_quantity,
                        'ux_cmds_c_bi' : self.do_cmds_prog_field_bint,
                        'ux_cmds_c_sq' : self.do_cmds_prog_field_quantity,
                        'ux_cmds_c_si' : self.do_cmds_prog_field_sint,
                        'ux_cmds_f_bq' : self.do_cmds_prog_field_quantity,
                        'ux_cmds_f_bi' : self.do_cmds_prog_field_bint,
                        'ux_cmds_f_sq' : self.do_cmds_prog_field_quantity,
                        'ux_cmds_f_si' : self.do_cmds_prog_field_sint,
                        'ux_bulls_select' : self.do_misc_dirty,
                        'ux_jhmcs_hud' : self.do_misc_dirty,
                        'ux_jhmcs_pit' : self.do_misc_dirty,
                        'ux_jhmcs_rwr' : self.do_misc_dirty,
                        'ux_jhmcs_dc_select' : self.do_misc_dirty,
                        'ux_tmplt_select' : self.do_template_select,
                        'ux_tmplt_save_as' : self.do_template_save_as,
                        'ux_tmplt_update' : self.do_template_update,
                        'ux_tmplt_delete' : self.do_template_delete,
        }

        tout_val = 1000000
        while True:
            new_event, new_values = self.window.Read(timeout=tout_val, timeout_key='ux_timeout')
            tout_val = 1000000
            if event != 'ux_timeout':
                self.logger.debug(f"AVS Event: {new_event} / {event}")
                self.logger.debug(f"AVS Values: {new_values}")
            if new_values is not None:
                self.values = new_values
            event = new_event

            if event != 'ux_done' and \
               event != PyGUI.WINDOW_CLOSE_ATTEMPTED_EVENT and \
               event is not None:
                self.update_gui_control_enable_state()
                for key_base in ['ux_nav', 'ux_air', 'ux_gnd', 'ux_dog']:
                    self.update_gui_enable_mfd_row(key_base)
                self.update_gui_enable_tacan_row()
                self.update_gui_enable_cmds()
            elif not self.is_dirty or \
                 PyGUI.PopupOKCancel(f"You have unsaved changes to the current template." +
                                     f" Closing the window will discard these changes.",
                                     title="Unsaved Changes") == "OK":
                    break

            if event != 'ux_timeout':
                try:
                    (handler_map[event])(event)
                except Exception as e:
                    pass
                    # self.logger.debug(f"AVS ERROR: {e}")
                tout_val = 0
        
        self.close()

    def close(self):
        self.window.close()