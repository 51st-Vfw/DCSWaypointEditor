'''
*
*  avionics_setup_viper_gui.py: DCS Waypoint Editor Avionics Setup (Viper)
*                               template editor GUI 
*
*  Copyright (C) 2022 twillis/ilominar
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
import json
import os
import PySimpleGUI as PyGUI

from pathlib import Path

from src.db_models import AvionicsSetupModel
from src.db_objects import AvionicsSetup
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

# Maps UI MFD format key base onto default MFD format setups (as of DCS v2.8.1.34437).
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


class AvionicsSetupViperGUI:

    def __init__(self, base_gui=None):
        self.logger = get_logger(__name__)
        self.base_gui = base_gui
        self.cur_cmds_prog_sel = "MAN 1"
        self.cur_cmds_prog_map = { }

        self.is_dirty = False

    # create the airframe-specific tab group for the avionics ui.
    #
    def af_create_tab_gui(self):
        mfd_formats = list(mfd_format_map.keys())

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

        layout_cmds_opt = [
            PyGUI.Checkbox("Only set CMDS program parameters when they differ from the default parameters (reduces setup time)",
                           key='ux_cmds_force', enable_events=True, size=(80,1), pad=(10,(0,12)))
        ]

        layout_cmds_tab = [
            PyGUI.Tab("CMDS",
                      [layout_cmds_sel, layout_cmds_prog_params, layout_cmds_prog_updates, layout_cmds_opt])
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

        # ---- Sharing

        layout_share_title = [
            PyGUI.Text("You can share avionics setups using export and import functions", pad=(12,12))
        ]

        layout_share = [
            PyGUI.Button("Export Setup to File...", key='ux_share_export', size=(20,1), pad=(12,0)),
            PyGUI.Button("Import Setup from File...", key='ux_share_import', size=(20,1), pad=(12,0))
        ]

        layout_share_tab = [
            PyGUI.Tab("Sharing", [layout_share_title, layout_share])
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

        return PyGUI.TabGroup([layout_mfd_tab,
                               layout_tacan_tab,
                               layout_cmds_tab,
                               layout_misc_tab,
                               layout_share_tab], pad=(8,8))

    # update the gui for the enable state of a MFD master mode
    #
    def update_gui_enable_mfd_row(self, key_base):
        if self.base_gui.values[f"{key_base}_ckbx"]:
            label_color = "#ffffff"
            for key_suffix in mfd_key_suffixes:
                self.base_gui.window[f"{key_base}{key_suffix}"].update(disabled=False)
        else:
            label_color = "#b8b8b8"
            self.base_gui.window[f"{key_base}_l14"].update(value="FCR", disabled=True)
            if key_base == 'ux_nav':
                self.base_gui.window[f"{key_base}_l13"].update(value="TEST", disabled=True)
                self.base_gui.window[f"{key_base}_l12"].update(value="DTE", disabled=True)
            elif key_base == 'ux_gnd' or key_base == 'ux_air':
                self.base_gui.window[f"{key_base}_l13"].update(value="FLCS", disabled=True)
                self.base_gui.window[f"{key_base}_l12"].update(value="TEST", disabled=True)
            else:
                self.base_gui.window[f"{key_base}_l13"].update(value="", disabled=True)
                self.base_gui.window[f"{key_base}_l12"].update(value="", disabled=True)
            self.base_gui.window[f"{key_base}_r14"].update(value="SMS", disabled=True)
            if key_base == 'ux_dog':
                self.base_gui.window[f"{key_base}_r13"].update(value="", disabled=True)
            else:
                self.base_gui.window[f"{key_base}_r13"].update(value="HSD", disabled=True)
            self.base_gui.window[f"{key_base}_r12"].update(value="", disabled=True)
        for key_suffix in mfd_key_suffixes:
            self.base_gui.window[f"{key_base}_txt{key_suffix}"].update(text_color=label_color)

    # update the gui to ensure a format appears only once in a master mode
    #
    def update_gui_unique_mfd_row(self, key, key_base):
        value = self.base_gui.values[key]
        for key_suffix in mfd_key_suffixes:
            row_key = f"{key_base}{key_suffix}"
            if row_key != key and self.base_gui.values[row_key] == value:
                self.base_gui.window[row_key].update(value="")

    # update the gui for the enable state of the tacan
    #
    def update_gui_enable_tacan_row(self):
        if self.base_gui.values['ux_tacan_ckbx']:
            label_color = "#ffffff"
            input_color = "#000000"
            chan = self.base_gui.values['ux_tacan_chan']
            if self.base_gui.values['ux_tacan_lw_select'] == "Wingman":
                chan = int(chan) + 63
            xy = self.base_gui.values['ux_tacan_xy_select']
            summary_txt = f" (setup will program TACAN to {chan}{xy} A/A)"
            self.base_gui.window['ux_tacan_chan'].update(disabled=False, text_color=input_color)
            self.base_gui.window['ux_tacan_xy_select'].update(disabled=False, readonly=True)
            self.base_gui.window['ux_tacan_lw_select'].update(disabled=False, readonly=True)
        else:
            label_color = "#b8b8b8"
            input_color = "#b8b8b8"
            summary_txt = ""
            self.base_gui.window['ux_tacan_chan'].update(disabled=True, text_color=input_color)
            self.base_gui.window['ux_tacan_xy_select'].update(disabled=True)
            self.base_gui.window['ux_tacan_lw_select'].update(disabled=True)
        self.base_gui.window['ux_tacan_role'].update(text_color=label_color)
        self.base_gui.window['ux_tacan_info'].update(summary_txt)

    # update the gui for the enable state of the cmds
    #
    def update_gui_enable_cmds(self):
        if self.base_gui.values['ux_cmds_reconfig']:
            label_color = "#ffffff"
            input_color = "#000000"
            disabled = False
        else:
            label_color = "#b8b8b8"
            input_color = "#b8b8b8"
            disabled = True
        for cmds_type in cmds_types:
            for cmds_param in cmds_params:
                self.base_gui.window[f"ux_cmds_{cmds_type}_{cmds_param}"].update(disabled=disabled,
                                                                                 text_color=input_color)
                self.base_gui.window[f"ux_cmds_{cmds_type}_{cmds_param}_t1"].update(text_color=label_color)
                self.base_gui.window[f"ux_cmds_{cmds_type}_{cmds_param}_t2"].update(text_color=label_color)
        prog_list = "None"
        for prog in [ 'MAN 1', 'MAN 2', 'MAN 3', 'MAN 4', 'Panic', 'Bypass']:
            if self.cur_cmds_prog_map[prog]:
                if prog_list == "None":
                    prog_list = prog
                else:
                    prog_list += f", {prog}"
        self.base_gui.window['ux_cmds_prog_update'].update(prog_list)


    # get/set mfd format row ui state
    #
    # the state is expressed in the database format (csv list of osb numbers, see the definition
    # of the f16_mfd_setup_* fields in the database model).
    #
    def get_gui_mfd_row(self, key_base):
        if self.base_gui.values[f"{key_base}_ckbx"] == False:
            config = None
        else:
            osb_list = []
            for key_suffix in mfd_key_suffixes:
                osb_list.append(mfd_format_map[self.base_gui.values[f"{key_base}{key_suffix}"]])
            config = ','.join([str(item) for item in osb_list])
        return config
    
    def set_gui_mfd_row(self, key_base, value):
        if value is None:
            self.base_gui.window[f"{key_base}_ckbx"].update(value=False)
            osb_list = copy.copy(mfd_default_setup_map[key_base])
        else:
            self.base_gui.window[f"{key_base}_ckbx"].update(value=True)
            osb_list = [ int(osb) for osb in value.split(",") ]
        for key_suffix in mfd_key_suffixes:
            osb = osb_list.pop(0)
            hits = [k for k,v in mfd_format_map.items() if v == osb]
            if (len(hits) == 0):
                hits = [""]
            self.base_gui.window[f"{key_base}{key_suffix}"].update(value=hits[0])

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
        if self.base_gui.values['ux_cmds_reconfig'] == True:
            value = ""
            sep = ""
            for cmds_type in cmds_types:
                for cmds_param in cmds_params:
                    value += sep
                    field = self.base_gui.values[f'ux_cmds_{cmds_type}_{cmds_param}']
                    value += cmds_params_val_map[cmds_param](field)
                    sep = ","
                sep = ";"
        else:
            value = None
        return value
    
    def set_gui_cmds_prog(self, value):
        if value is None:
            self.base_gui.window['ux_cmds_reconfig'].update(value=False)
            self.base_gui.values['ux_cmds_reconfig'] = False
            for cmds_type in cmds_types:
                for cmds_param in cmds_params:
                    self.base_gui.window[f"ux_cmds_{cmds_type}_{cmds_param}"].update("")
        else:
            print(f"CMDS f{value}")
            self.base_gui.window['ux_cmds_reconfig'].update(value=True)
            self.base_gui.values['ux_cmds_reconfig'] = True
            types = value.split(";")
            c_params = types[0].split(",")
            f_params = types[1].split(",")

            self.base_gui.window['ux_cmds_c_bq'].update(f"{int(c_params[0]):#d}")
            self.base_gui.window['ux_cmds_c_bi'].update(f"{float(c_params[1]):#0.3f}")
            self.base_gui.window['ux_cmds_c_sq'].update(f"{int(c_params[2]):#d}")
            self.base_gui.window['ux_cmds_c_si'].update(f"{float(c_params[3]):#0.2f}")

            self.base_gui.window['ux_cmds_f_bq'].update(f"{int(f_params[0]):#d}")
            self.base_gui.window['ux_cmds_f_bi'].update(f"{float(f_params[1]):#0.3f}")
            self.base_gui.window['ux_cmds_f_sq'].update(f"{int(f_params[2]):#d}")
            self.base_gui.window['ux_cmds_f_si'].update(f"{float(f_params[3]):#0.2f}")
        self.update_gui_enable_cmds()
        

    # synchronize TACAN setup UI and database
    #
    def copy_tacan_core_to_ui(self, tacan_yard):
        if tacan_yard is None:
            self.base_gui.window['ux_tacan_ckbx'].update(value=False)
            self.base_gui.window['ux_tacan_chan'].update("1")
            self.base_gui.window['ux_tacan_xy_select'].update(value="X")
            self.base_gui.window['ux_tacan_lw_select'].update(value="Flight Lead")
        else:
            fields = [ str(field) for field in tacan_yard.split(",") ]
            if fields[2] == "L":
                role_index = 0
            else:
                role_index = 1
            self.base_gui.window['ux_tacan_ckbx'].update(value=True)
            self.base_gui.window['ux_tacan_chan'].update(fields[0])
            self.base_gui.window['ux_tacan_xy_select'].update(value=fields[1])
            self.base_gui.window['ux_tacan_lw_select'].update(set_to_index=role_index)

    def copy_tacan_dbase_to_ui(self, db_model=None):
        if db_model is not None:
            self.copy_tacan_core_to_ui(db_model.tacan_yard)
        else:
            self.copy_tacan_core_to_ui(None)
        self.is_dirty = False

    def copy_tacan_ui_to_dbase(self, db_model=None, db_save=True):
        if db_model is not None:
            if self.base_gui.values['ux_tacan_ckbx'] == False:
                tacan_yard = None
            else:
                chan = int(self.base_gui.values['ux_tacan_chan'])
                xy = self.base_gui.values['ux_tacan_xy_select']
                if self.base_gui.values['ux_tacan_lw_select'] == "Flight Lead":
                    lw = "L"
                else:
                    lw = "W"
                tacan_yard = f"{chan},{xy},{lw}"
            db_model.tacan_yard = tacan_yard
            if db_save:
                try:
                    db_model.save()
                except:
                    PyGUI.PopupError("Unable to save TACAN yardstick information to database?")
            self.is_dirty = False
    

    # synchronize F-16 MFD setup UI and database
    #
    def copy_f16_mfd_core_to_ui(self, setup_nav, setup_air, setup_gnd, setup_dog, setup_opt):
        self.set_gui_mfd_row('ux_nav', setup_nav)
        self.set_gui_mfd_row('ux_air', setup_air)
        self.set_gui_mfd_row('ux_gnd', setup_gnd)
        self.set_gui_mfd_row('ux_dog', setup_dog)
        self.base_gui.window['ux_mfd_force'].update(value=setup_opt)

    def copy_f16_mfd_dbase_to_ui(self, db_model=None):
        if db_model is not None:
            self.copy_f16_mfd_core_to_ui(db_model.f16_mfd_setup_nav, db_model.f16_mfd_setup_air,
                                         db_model.f16_mfd_setup_gnd, db_model.f16_mfd_setup_dog,
                                         db_model.f16_mfd_setup_opt)
        else:
            self.copy_f16_mfd_core_to_ui(None, None, None, None, False)
        self.is_dirty = False
    
    def copy_f16_mfd_ui_to_dbase(self, db_model=None, db_save=True):
        if db_model is not None:
            db_model.f16_mfd_setup_nav = self.get_gui_mfd_row('ux_nav')
            db_model.f16_mfd_setup_air = self.get_gui_mfd_row('ux_air')
            db_model.f16_mfd_setup_gnd = self.get_gui_mfd_row('ux_gnd')
            db_model.f16_mfd_setup_dog = self.get_gui_mfd_row('ux_dog')
            db_model.f16_mfd_setup_opt = self.base_gui.values['ux_mfd_force']
            if db_save:
                try:
                    db_model.save()
                except:
                    PyGUI.PopupError("Unable to save MFD setup information to database?")
            self.is_dirty = False


    # synchronize F-16 CMDS setup UI and database
    #
    def copy_f16_cmds_core_to_ui(self, cur_prog, p1, p2, p3, p4, p5, p6, opt):
        if cur_prog is None:
            cur_prog = self.base_gui.values['ux_cmds_prog_sel']
        self.cur_cmds_prog_map['MAN 1'] = p1
        self.cur_cmds_prog_map['MAN 2'] = p2
        self.cur_cmds_prog_map['MAN 3'] = p3
        self.cur_cmds_prog_map['MAN 4'] = p4
        self.cur_cmds_prog_map['Panic'] = p5
        self.cur_cmds_prog_map['Bypass'] = p6
        self.base_gui.window['ux_cmds_force'].update(value=opt)
        self.set_gui_cmds_prog(self.cur_cmds_prog_map[cur_prog])

    def copy_f16_cmds_dbase_to_ui(self, db_model=None, cur_prog=None):
        if db_model is not None:
            self.copy_f16_cmds_core_to_ui(cur_prog,
                                          db_model.f16_cmds_setup_p1, db_model.f16_cmds_setup_p2,
                                          db_model.f16_cmds_setup_p3, db_model.f16_cmds_setup_p4,
                                          db_model.f16_cmds_setup_p5, db_model.f16_cmds_setup_p6,
                                          db_model.f16_cmds_setup_opt)
        else:
            self.copy_f16_cmds_core_to_ui(cur_prog, None, None, None, None, None, None, False)
        self.is_dirty = False
    
    def copy_f16_cmds_ui_to_dbase(self, db_model=None, cur_prog=None, db_save=True):
        if cur_prog is None:
            cur_prog = self.base_gui.values['ux_cmds_prog_sel']
        self.cur_cmds_prog_map[cur_prog] = self.get_gui_cmds_prog()
        if db_model is not None:
            db_model.f16_cmds_setup_p1 = self.cur_cmds_prog_map['MAN 1']
            db_model.f16_cmds_setup_p2 = self.cur_cmds_prog_map['MAN 2']
            db_model.f16_cmds_setup_p3 = self.cur_cmds_prog_map['MAN 3']
            db_model.f16_cmds_setup_p4 = self.cur_cmds_prog_map['MAN 4']
            db_model.f16_cmds_setup_p5 = self.cur_cmds_prog_map['Panic']
            db_model.f16_cmds_setup_p6 = self.cur_cmds_prog_map['Bypass']
            db_model.f16_cmds_setup_opt = self.base_gui.values['ux_cmds_force']
            if db_save:
                try:
                    db_model.save()
                except:
                    PyGUI.PopupError("Unable to save CMDS setup information to database?")
            self.copy_f16_cmds_dbase_to_ui(db_model)


    # synchronize F-16 Miscellaneous setup UI and database
    #
    def copy_f16_misc_core_to_ui(self, bulls, jhmcs):
        if bulls is None:
            self.base_gui.window['ux_bulls_select'].update(set_to_index=0)
        else:
            self.base_gui.window['ux_bulls_select'].update(set_to_index=bulls)
        if jhmcs is None:
            self.base_gui.window['ux_jhmcs_hud'].update(value=True)
            self.base_gui.window['ux_jhmcs_pit'].update(value=True)
            self.base_gui.window['ux_jhmcs_rwr'].update(value=True)
            self.base_gui.window['ux_jhmcs_dc_select'].update(set_to_index=0)
        else:
            fields = [ int(field) for field in jhmcs.split(",") ]
            self.base_gui.window['ux_jhmcs_hud'].update(value=bool(fields[0]))
            self.base_gui.window['ux_jhmcs_pit'].update(value=bool(fields[1]))
            self.base_gui.window['ux_jhmcs_rwr'].update(value=bool(fields[2]))
            self.base_gui.window['ux_jhmcs_dc_select'].update(set_to_index=fields[3])

    def copy_f16_misc_dbase_to_ui(self, db_model=None):
        if db_model is not None:
            self.copy_f16_misc_core_to_ui(db_model.f16_bulls_setup, db_model.f16_jhmcs_setup)
        else:
            self.copy_f16_misc_core_to_ui(None, None)
        self.is_dirty = False

    def copy_f16_misc_ui_to_dbase(self, db_model=None, db_save=True):
        if db_model is not None:
            if self.base_gui.values['ux_bulls_select'] == "Ownship Bullseye":
                db_model.f16_bulls_setup = "1"
            else:
                db_model.f16_bulls_setup = None

            hud = int(self.base_gui.values['ux_jhmcs_hud'])
            pit = int(self.base_gui.values['ux_jhmcs_pit'])
            rwr = int(self.base_gui.values['ux_jhmcs_rwr'])
            dcs = jhmcs_dc_setup_map[self.base_gui.values['ux_jhmcs_dc_select']]
            jhmcs_setup = f"{hud},{pit},{rwr},{dcs}"
            if jhmcs_setup != "1,1,1,0":
                db_model.f16_jhmcs_setup = jhmcs_setup
            else:
                db_model.f16_jhmcs_setup = None

            if db_save:
                try:
                    db_model.save()
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
        if self.base_gui.values[event]:
            try:
                input_as_int = int(self.base_gui.values[event])
                if input_as_int < 1 or input_as_int > 63:
                    raise ValueError("Out of bounds")
                self.is_dirty = True
            except:
                PyGUI.Popup("The TACAN channel must be between 1 and 63 for use as a yardstick.",
                            title="Invalid Channel")
                self.base_gui.window[event].update(self.base_gui.values[event][:-1])

    def do_cmds_reconfig(self, event):
        cur_prog = self.base_gui.values['ux_cmds_prog_sel']
        if self.base_gui.values[event] == True:
            program = cmds_prog_default_map[cur_prog]
        else:
            program = None
        self.cur_cmds_prog_map[cur_prog] = program
        self.set_gui_cmds_prog(program)
        self.is_dirty = True
    
    def do_cmds_prog_select(self, event):
        self.cur_cmds_prog_map[self.cur_cmds_prog_sel] = self.get_gui_cmds_prog()
        self.cur_cmds_prog_sel = self.base_gui.values[event]
        self.set_gui_cmds_prog(self.cur_cmds_prog_map[self.cur_cmds_prog_sel])

    def do_cmds_prog_field_quantity(self, event):
        if self.base_gui.values[event]:
            if self.val_cmds_prog_field_quantity(self.base_gui.values[event]):
                self.is_dirty = True
            else:
                self.base_gui.window[event].update(self.base_gui.values[event][:-1])

    def do_cmds_prog_field_bint(self, event):
        if self.base_gui.values[event]:
            if self.val_cmds_prog_field_bint(self.base_gui.values[event]):
                self.is_dirty = True
            else:
                self.base_gui.window[event].update(self.base_gui.values[event][:-1])

    def do_cmds_prog_field_sint(self, event):
        if self.base_gui.values[event]:
            if self.val_cmds_prog_field_sint(self.base_gui.values[event]):
                self.is_dirty = True
            else:
                self.base_gui.window[event].update(self.base_gui.values[event][:-1])

    def do_cmds_force(self, event):
        self.is_dirty = True

    def do_misc_dirty(self, event):
        self.is_dirty = True

    def do_share_export(self, event):
        name = self.base_gui.cur_av_setup
        initial_folder = str(Path.home())
        default_path = initial_folder + "\\avionics_setup.json"
        path = PyGUI.PopupGetFile("Specify a File to Export To",
                                      f"Exporting Avionics Setup '{name}'",
                                      initial_folder=initial_folder,
                                      default_path=default_path,
                                      default_extension=".json", save_as=True,
                                      file_types=(("JSON File", "*.json"),))
        if path is not None:
            av_setup = AvionicsSetup(self.base_gui.cur_av_setup, self.base_gui.airframe)
            if not path.endswith(".json"):
                path += ".json"
            with open(path, "w+") as f:
                f.write(str(av_setup))
            PyGUI.Popup(f"Avionics setup '{name}' successfullly written to '{path}'.")
    
    def do_share_import(self, event):
        if self.is_dirty:
            action = PyGUI.PopupOKCancel(f"You have unsaved changes to the current settings." +
                                         f" Importing will over-write these changes.",
                                         title="Unsaved Changes")
        else:
            action = PyGUI.PopupOKCancel(f"Importing will over-write the current settings with" +
                                         f" the values from the import file.",
                                         title="Overwrite Settings")
        if action == "OK":
            path = PyGUI.PopupGetFile("Select a File to Import From",
                                    "Importing Avionics Settings from File")
            if path is not None and len(path) > 0:
                try:
                    with open(path, "rb") as f:
                        data = f.read()
                    str = data.decode("UTF-8")
                    avs_dict = json.loads(str)

                    self.copy_tacan_core_to_ui(avs_dict.get('tacan_yard'))
                    self.copy_f16_mfd_core_to_ui(avs_dict.get('f16_mfd_setup_nav'),
                                                 avs_dict.get('f16_mfd_setup_air'),
                                                 avs_dict.get('f16_mfd_setup_gnd'),
                                                 avs_dict.get('f16_mfd_setup_dog'),
                                                 avs_dict.get('f16_mfd_setup_opt'))
                    self.copy_f16_cmds_core_to_ui(None,
                                                  avs_dict.get('f16_cmds_setup_p1'),
                                                  avs_dict.get('f16_cmds_setup_p2'),
                                                  avs_dict.get('f16_cmds_setup_p3'),
                                                  avs_dict.get('f16_cmds_setup_p4'),
                                                  avs_dict.get('f16_cmds_setup_p5'),
                                                  avs_dict.get('f16_cmds_setup_p6'),
                                                  avs_dict.get('f16_cmds_setup_opt'))
                    self.copy_f16_misc_core_to_ui(avs_dict.get('f16_bulls_setup'),
                                                  avs_dict.get('f16_jhmcs_setup'))

                    PyGUI.Popup(f"Avionics setup '{self.base_gui.cur_av_setup}' successfullly" +
                                f" imported from '{path}'.")
                    self.is_dirty = True

                except:
                    file = os.path.split(path)[1]
                    PyGUI.Popup(f"Failed to parse the file '{file}' for import.",
                                title="Import Fails")
                    self.is_dirty = False
                    self.base_gui.values['ux_tmplt_select'] = "DCS Default"
                    self.base_gui.window['ux_tmplt_select'].update(value="DCS Default")
                    self.base_gui.do_template_select(None)

            elif path is not None and len(path) == 0:
                PyGUI.Popup(f"There was no file specified to import.", title="Import Fails")

    # field validation
    #
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

    # airframe-specific template select handler. the core avionics setup code will handle confirming change to
    # dirty templates.
    #
    def af_do_template_select(self, event):
        self.cur_cmds_prog_sel = 'MAN 1'
        self.base_gui.window['ux_cmds_prog_sel'].update(value=self.cur_cmds_prog_sel)

        self.copy_f16_cmds_dbase_to_ui(self.base_gui.dbase_setup)
        self.copy_f16_mfd_dbase_to_ui(self.base_gui.dbase_setup)
        self.copy_f16_misc_dbase_to_ui(self.base_gui.dbase_setup)
        self.copy_tacan_dbase_to_ui(self.base_gui.dbase_setup)

    # airframe-specific template save as handler. the core avionics setup code will determine the name to save as
    # and wrap the call in a try/except block to catch failures.
    #
    def af_do_template_save_as(self, event, name):
        self.base_gui.dbase_setup = AvionicsSetupModel.create(name=name)
        self.copy_f16_cmds_ui_to_dbase(self.base_gui.dbase_setup, None, False)
        self.copy_f16_mfd_ui_to_dbase(self.base_gui.dbase_setup, False)
        self.copy_f16_misc_ui_to_dbase(self.base_gui.dbase_setup, False)
        self.copy_tacan_ui_to_dbase(self.base_gui.dbase_setup, True)

    # airframe-specific template update handler. this should not be called on r/o templates (such as the default
    # template).
    #
    def af_do_template_update(self, event):
        self.copy_f16_cmds_ui_to_dbase(self.base_gui.dbase_setup, None, True)
        self.copy_f16_mfd_ui_to_dbase(self.base_gui.dbase_setup, True)
        self.copy_f16_misc_ui_to_dbase(self.base_gui.dbase_setup, True)
        self.copy_tacan_ui_to_dbase(self.base_gui.dbase_setup, True)

    # airframe-specific template delete. the core avionics setup code checks with the user prior to calling this
    # method and will wrap the call in a try/except block to catch failures.
    #
    def af_do_template_delete(self, event):
        self.base_gui.dbase_setup.delete_instance()
        self.base_gui.dbase_setup = None
        self.is_dirty = False
        self.cur_cmds_prog_sel = 'MAN 1'
        self.base_gui.window['ux_cmds_prog_sel'].update(value=self.cur_cmds_prog_sel)
        self.copy_f16_cmds_dbase_to_ui(self.base_gui.dbase_setup)
        self.copy_f16_mfd_dbase_to_ui(self.base_gui.dbase_setup)
        self.copy_f16_misc_dbase_to_ui(self.base_gui.dbase_setup)
        self.copy_tacan_dbase_to_ui(self.base_gui.dbase_setup)

    # helper method to copy values from the database to the ui. current window ui values should be installed prior
    # to calling this method.
    #
    def af_copy_dbase_to_ui(self):
        self.copy_f16_cmds_dbase_to_ui(self.base_gui.dbase_setup)
        self.copy_f16_mfd_dbase_to_ui(self.base_gui.dbase_setup)
        self.copy_f16_misc_dbase_to_ui(self.base_gui.dbase_setup)
        self.copy_tacan_dbase_to_ui(self.base_gui.dbase_setup)

    # helper method to prepare the airframe gui to run. current window ui values should be installed prior to
    # calling this method. returns a map of ui events to handler functions. the core avionics setup code wraps this
    # call in a try/except block to catch failures.
    #
    def af_update_gui(self):
        for key_base in ['ux_nav', 'ux_gnd', 'ux_air', 'ux_dog']:
            self.update_gui_enable_mfd_row(key_base)
        self.update_gui_enable_tacan_row()
        self.update_gui_enable_cmds()

    # helper method to return the handler map for the ui. the map has keys of ux events and values of functions
    # to handle the event.
    #
    def af_get_handler_map(self):
        return { 'ux_nav_ckbx' : self.do_mfd_osb_ckbx,
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
                 'ux_cmds_force' : self.do_cmds_force,
                 'ux_bulls_select' : self.do_misc_dirty,
                 'ux_jhmcs_hud' : self.do_misc_dirty,
                 'ux_jhmcs_pit' : self.do_misc_dirty,
                 'ux_jhmcs_rwr' : self.do_misc_dirty,
                 'ux_jhmcs_dc_select' : self.do_misc_dirty,
                 'ux_share_export' : self.do_share_export,
                 'ux_share_import' : self.do_share_import,
        }

    # helper method to update airframe-specific gui state.
    #
    def af_update_gui_state(self):
        for key_base in ['ux_nav', 'ux_air', 'ux_gnd', 'ux_dog']:
            self.update_gui_enable_mfd_row(key_base)
        self.update_gui_enable_tacan_row()
        self.update_gui_enable_cmds()
