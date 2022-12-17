'''
*
*  avionics_setup.py: DCS Waypoint Editor Avionics Setup template editor GUI 
*
*  Copyright (C) 2021-22 twillis/ilominar
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

from src.avionics_setup_viper_gui import AvionicsSetupViperGUI
from src.db_models import AvionicsSetupModel
from src.gui_util import airframe_type_to_ui_text
from src.logger import get_logger


class AvionicsSetupGUI:

    def __init__(self, airframe=None, cur_av_setup=None):
        self.logger = get_logger(__name__)
        self.dbase_setup = None
        self.values = None
        self.airframe = airframe
        self.cur_av_setup = cur_av_setup

        if self.cur_av_setup is not None:
            try:
                self.dbase_setup = AvionicsSetupModel.get(AvionicsSetupModel.name == self.cur_av_setup)
            except:
                self.cur_av_setup = "DCS Default"
        else:
            self.cur_av_setup = "DCS Default"

        self.window = self.create_gui(airframe)

    def is_setup_default(self):
        if self.values.get('ux_tmplt_select') == "DCS Default":
            return True
        return False

    def create_gui(self, airframe="viper"):
        airframe_ui = airframe_type_to_ui_text(airframe)

        if airframe == "viper":
            self.airframe_gui = AvionicsSetupViperGUI(self)

        # ---- Core Airframe TabGroup

        layout_core_tgroup = self.airframe_gui.af_create_tab_gui()

        # ---- Common Management Controls

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
                            [[layout_core_tgroup],
                             [layout_mgmt]],
                            enable_close_attempted_event=True, modal=True, finalize=True)


    # update the gui state based on a change to the template list
    #
    def update_gui_template_list(self):
        # TODO: once multiple airframes come into play, limit list to only select airframes (?)
        # tmplts = [ "DCS Default" ] + AvionicsSetupModel.list_all_names_for_airframe(self.airframe)
        tmplts = [ "DCS Default" ] + AvionicsSetupModel.list_all_names()
        if self.dbase_setup is None:
            cur_av_setup = "DCS Default"
        else:
            cur_av_setup = self.dbase_setup.name
        self.window['ux_tmplt_select'].update(values=tmplts, set_to_index=tmplts.index(cur_av_setup))
        self.values['ux_tmplt_select'] = cur_av_setup
        self.update_gui_template_control_enable_state()

    # update the gui button state based on current setup
    #
    def update_gui_template_control_enable_state(self):
        if self.airframe_gui.is_dirty:
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


    # gui action handlers
    #
    def do_template_select(self, event):
        if self.airframe_gui.is_dirty:
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
        
        self.airframe_gui.af_do_template_select(event, self.dbase_setup)

    def do_template_save_as(self, event):
        name = PyGUI.PopupGetText("Template Name", "Creating New Template")
        if name is not None:
            try:
                self.airframe_gui.af_do_template_save_as(event, name)
                self.update_gui_template_list()
            except:
                PyGUI.Popup(f"Unable to create a template named '{name}'. Is there already" +
                             " a template with that name?", title="Error")

    def do_template_update(self, event):
        if not self.is_setup_default():
            self.airframe_gui.af_do_template_update(event)

    def do_template_delete(self, event):
        action = PyGUI.PopupOKCancel(f"Are you sure you want to delete the settings {self.cur_av_setup}?",
                                     title="Confirm Delete")
        if action == "OK":
            try:
                self.airframe_gui.af_do_template_delete(event)
                self.update_gui_template_list()
            except Exception as e:
                PyGUI.PopupError(f"Unable to delete the settings {self.cur_av_setup} from the database.")


    # run the gui for the preferences window.
    #
    def run(self):
        self.window.disappear()

        try:
            event, self.values = self.window.read(timeout=0)
            self.airframe_gui.af_copy_dbase_to_ui()

            event, self.values = self.window.read(timeout=0)
            self.airframe_gui.af_update_gui()
    
            self.update_gui_template_list()
        except Exception as e:
            self.logger.debug(f"AVS setup fails {e}")
            # TODO: error dialog?

        self.window.reappear()

        handler_map = { 'ux_tmplt_select' : self.do_template_select,
                        'ux_tmplt_save_as' : self.do_template_save_as,
                        'ux_tmplt_update' : self.do_template_update,
                        'ux_tmplt_delete' : self.do_template_delete,
        }
        handler_map.update(self.airframe_gui.af_get_handler_map())

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
                self.update_gui_template_control_enable_state()
                self.airframe_gui.af_update_gui_state()
            elif not self.airframe_gui.is_dirty or \
                 PyGUI.PopupOKCancel(f"You have unsaved changes to the current template." +
                                     f" Closing the window will discard these changes.",
                                     title="Unsaved Changes") == "OK":
                break

            if event != 'ux_timeout':
                try:
                    (handler_map[event])(event)
                except Exception as e:
                    # self.logger.debug(f"AVS ERROR: {e}")
                    pass
                tout_val = 0
        
        self.close()

    def close(self):
        self.window.close()