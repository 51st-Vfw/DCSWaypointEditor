'''
*
*  prefs.py: DCS Waypoint Editor preferences model/object
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
import re

from configparser import ConfigParser
from pathlib import Path
from src.gui_util import airframe_type_to_ui_text
from src.logger import get_logger


logger = get_logger(__name__)


# preferences object to abstract preferences storage. preference values are always strings.
#
class Preferences:
    def __init__(self, data_path=".\\"):
        self.path_data = data_path
        self.path_ini = data_path + "settings.ini"
        self.path_profile_db = data_path + "profiles.db"

        self.prefs = ConfigParser()
        self.prefs.add_section("PREFERENCES")
        self.reset_prefs()

        try:
            open(self.path_ini, "r").close()
            self.synchronize_prefs()
        except FileNotFoundError:
            self.persist_prefs()

    # ================ setup support

    @staticmethod
    def locate_dcswe_prefs():
        if os.path.exists(".\\settings.ini"):
            data_path = ".\\"
        elif os.path.exists(f"{Path.home()}\\Documents\\DCSWE\\settings.ini"):
            data_path = f"{Path.home()}\\Documents\\DCSWE" + "\\"
        else:
            data_path = None
        return data_path

    def prefs_to_file(self, path):
        with open(path, "w+") as f:
            f.write("---- settings.ini ----\n\n")
            with open(self.path_ini, "r") as f2:
                f.writelines(f2.readlines())
            f.write("----------------------\n\n")

    # ================ general properties

    @property
    def prefs(self):
        return self._prefs
    
    @prefs.setter
    def prefs(self, value):
        self._prefs = value

    # ================ preferences properties

    @property
    def path_dcs(self):
        return self._path_dcs
    
    @path_dcs.setter
    def path_dcs(self, value):
        if value is not None and not value.endswith("\\") and not value.endswith("/"):
            value = value + "\\"
        self._path_dcs = value

    @property
    def path_tesseract(self):
        return self._path_tesseract

    @path_tesseract.setter
    def path_tesseract(self, value):
        self._path_tesseract = value

    @property
    def path_mission(self):
        return self._path_mission
    
    @path_mission.setter
    def path_mission(self, value):
        self._path_mission = value

    @property
    def dcs_btn_rel_delay_short(self):
        return self._dcs_btn_rel_delay_short

    @dcs_btn_rel_delay_short.setter
    def dcs_btn_rel_delay_short(self, value):
        if float(value) <= 0.0:
            raise ValueError("Short button release delay must be larger than zero")
        self._dcs_btn_rel_delay_short = value

    @property
    def dcs_btn_rel_delay_medium(self):
        return self._dcs_btn_rel_delay_medium

    @dcs_btn_rel_delay_medium.setter
    def dcs_btn_rel_delay_medium(self, value):
        if float(value) <= 0.0:
            raise ValueError("Medium button release delay must be larger than zero")
        self._dcs_btn_rel_delay_medium = value

    @property
    def hotkey_capture(self):
        return self._hotkey_capture
    
    @hotkey_capture.setter
    def hotkey_capture(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_capture = value

    @property
    def hotkey_capture_mode(self):
        return self._hotkey_capture_mode
    
    @hotkey_capture_mode.setter
    def hotkey_capture_mode(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_capture_mode = value

    @property
    def hotkey_enter_profile(self):
        return self._hotkey_enter_profile
    
    @hotkey_enter_profile.setter
    def hotkey_enter_profile(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_enter_profile = value

    @property
    def hotkey_enter_mission(self):
        return self._hotkey_enter_mission
    
    @hotkey_enter_mission.setter
    def hotkey_enter_mission(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_enter_mission = value

    @property
    def hotkey_item_sel_type_toggle(self):
        return self._hotkey_item_sel_type_toggle
    
    @hotkey_item_sel_type_toggle.setter
    def hotkey_item_sel_type_toggle(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_item_sel_type_toggle = value

    @property
    def hotkey_item_sel_advance(self):
        return self._hotkey_item_sel_advance
    
    @hotkey_item_sel_advance.setter
    def hotkey_item_sel_advance(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_item_sel_advance = value

    @property
    def hotkey_dgft_cycle(self):
        return self._hotkey_dgft_cycle
    
    @hotkey_dgft_cycle.setter
    def hotkey_dgft_cycle(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_dgft_cycle = value

    @property
    def airframe_default(self):
        return self._airframe_default
    
    @airframe_default.setter
    def airframe_default(self, value):
        if airframe_type_to_ui_text(value) is None:
            raise ValueError("Unknown airframe type")
        self._airframe_default = value

    @property
    def av_setup_default(self):
        return self._av_setup_default
    
    @av_setup_default.setter
    def av_setup_default(self, value):
        self._av_setup_default = value

    @property
    def callsign_default(self):
        return self._callsign_default
    
    @callsign_default.setter
    def callsign_default(self, value):
        if not self.is_callsign_valid(value):
            raise ValueError("Invalid callsign")
        self._callsign_default = value

    @property
    def is_auto_upd_check(self):
        return self._is_auto_upd_check

    @property
    def is_auto_upd_check_bool(self):
        return True if self._is_auto_upd_check == "true" else False

    @is_auto_upd_check.setter
    def is_auto_upd_check(self, value):
        if type(value) == bool or type(value) == int or type(value) == float:
            value = "true" if value == True else "false"
        self._is_auto_upd_check = value

    @property
    def is_tesseract_debug(self):
        return self._is_tesseract_debug

    @property
    def is_tesseract_debug_bool(self):
        return True if self._is_tesseract_debug == "true" else False

    @is_tesseract_debug.setter
    def is_tesseract_debug(self, value):
        if type(value) == bool or type(value) == int or type(value) == float:
            value = "true" if value else "false"
        self._is_tesseract_debug = value

    @property
    def is_av_setup_for_unk(self):
        return self._is_av_setup_for_unk

    @property
    def is_av_setup_for_unk_bool(self):
        return True if self._is_av_setup_for_unk == "true" else False

    @is_av_setup_for_unk.setter
    def is_av_setup_for_unk(self, value):
        if type(value) == bool or type(value) == int or type(value) == float:
            value = "true" if value else "false"
        self._is_av_setup_for_unk = value

    @property
    def is_f10_elev_clamped(self):
        return self._is_f10_elev_clamped

    @property
    def is_f10_elev_clamped_bool(self):
        return True if self._is_f10_elev_clamped == "true" else False

    @is_f10_elev_clamped.setter
    def is_f10_elev_clamped(self, value):
        if type(value) == bool or type(value) == int or type(value) == float:
            value = "true" if value else "false"
        self._is_f10_elev_clamped = value

    @property
    def is_load_auto_quit(self):
        return self._is_load_auto_quit

    @property
    def is_load_auto_quit_bool(self):
        return True if self._is_load_auto_quit == "true" else False

    @is_load_auto_quit.setter
    def is_load_auto_quit(self, value):
        if type(value) == bool or type(value) == int or type(value) == float:
            value = "true" if value else "false"
        self._is_load_auto_quit = value

    @property
    def is_disable_export(self):
        return self._is_disable_export

    @property
    def is_disable_export_bool(self):
        return True if self._is_disable_export == "true" else False

    @is_disable_export.setter
    def is_disable_export(self, value):
        if type(value) == bool or type(value) == int or type(value) == float:
            value = "true" if value else "false"
        self._is_disable_export = value

    @property
    def last_profile_sel(self):
        return self._last_profile_sel

    @last_profile_sel.setter
    def last_profile_sel(self, value):
        self._last_profile_sel = value

    # ================ general methods

    # validate a hot key sequence
    #
    def is_hotkey_valid(self, hotkey):
        if hotkey is not None and hotkey != "":
            tokens = hotkey.replace(" ", "+").split("+")
            if len(tokens) >= 1:
                key = tokens.pop()
                if key is None or len(key) != 1:
                    return False
                for token in tokens:
                    if token.lower() not in ("ctrl", "alt", "shift", "left", "right"):
                        return False
            else:
                return False
        return True

    # validate a callsign
    #
    def is_callsign_valid(self, callsign):
        if callsign != "" and not re.match(r"^[\D]+[\d]+-[\d]+$", callsign):
            return False
        else:
            return True

    # reset the preferences to their default values, must persist via persist_prefs to save.
    #
    def reset_prefs(self):
        self.path_dcs = f"{str(Path.home())}\\Saved Games\\DCS.openbeta" + "\\"
        self.path_tesseract = f"{os.environ['PROGRAMW6432']}\\Tesseract-OCR\\tesseract.exe"
        self.path_mission = f"{str(Path.home())}\\Desktop\\cf_mission.xml"
        self.dcs_btn_rel_delay_short = "0.15"
        self.dcs_btn_rel_delay_medium = "0.40"
        self.hotkey_capture = "ctrl+t"
        self.hotkey_capture_mode = "ctrl+shift+t"
        self.hotkey_enter_profile = "ctrl+alt+t"
        self.hotkey_enter_mission = "ctrl+alt+shift+t"
        self.hotkey_item_sel_type_toggle = "ctrl+alt+a"
        self.hotkey_item_sel_advance = "ctrl+alt+z"
        self.hotkey_dgft_cycle = "left ctrl+3"
        self.airframe_default = "viper"
        self.av_setup_default = "DCS Default"
        self.callsign_default = "Colt1-1"
        self.is_auto_upd_check = "true"
        self.is_tesseract_debug = "false"
        self.is_av_setup_for_unk = "true"
        self.is_f10_elev_clamped = "true"
        self.is_load_auto_quit = "false"
        self.is_disable_export = "false"
        self.last_profile_sel = ""

    # synchronize the preferences the backing store file
    #
    def synchronize_prefs(self):
        try:
            self.persist_prefs(do_write=False)
            self.prefs.read(self.path_ini)

            self.path_dcs = self.prefs["PREFERENCES"]["path_dcs"]
            self.path_tesseract = self.prefs["PREFERENCES"]["path_tesseract"]
            self.path_mission = self.prefs["PREFERENCES"]["path_mission"]
            self.dcs_btn_rel_delay_short = self.prefs["PREFERENCES"]["dcs_btn_rel_delay_short"]
            self.dcs_btn_rel_delay_medium = self.prefs["PREFERENCES"]["dcs_btn_rel_delay_medium"]
            self.hotkey_capture = self.prefs["PREFERENCES"]["hotkey_capture"]
            self.hotkey_capture_mode = self.prefs["PREFERENCES"]["hotkey_capture_mode"]
            self.hotkey_enter_profile = self.prefs["PREFERENCES"]["hotkey_enter_profile"]
            self.hotkey_enter_mission = self.prefs["PREFERENCES"]["hotkey_enter_mission"]
            self.hotkey_item_sel_type_toggle = self.prefs["PREFERENCES"]["hotkey_item_sel_type_toggle"]
            self.hotkey_item_sel_advance = self.prefs["PREFERENCES"]["hotkey_item_sel_advance"]
            self.hotkey_dgft_cycle = self.prefs["PREFERENCES"]["hotkey_dgft_cycle"]
            self.airframe_default = self.prefs["PREFERENCES"]["airframe_default"]
            self.av_setup_default = self.prefs["PREFERENCES"]["av_setup_default"]
            self.callsign_default = self.prefs["PREFERENCES"]["callsign_default"]
            self.is_auto_upd_check = self.prefs["PREFERENCES"]["is_auto_upd_check"]
            self.is_tesseract_debug = self.prefs["PREFERENCES"]["is_tesseract_debug"]
            self.is_av_setup_for_unk = self.prefs["PREFERENCES"]["is_av_setup_for_unk"]
            self.is_f10_elev_clamped = self.prefs["PREFERENCES"]["is_f10_elev_clamped"]
            self.is_load_auto_quit = self.prefs["PREFERENCES"]["is_load_auto_quit"]
            self.is_disable_export = self.prefs["PREFERENCES"]["is_disable_export"]
            self.last_profile_sel = self.prefs["PREFERENCES"]["last_profile_sel"]
        except:
            logger.error("Synchronize failed, resetting preferences to defaults")
            self.reset_prefs()

    # persist the preferences to the backing store file
    #
    def persist_prefs(self, do_write=True):
        self.prefs["PREFERENCES"]["path_dcs"] = self.path_dcs
        self.prefs["PREFERENCES"]["path_tesseract"] = self.path_tesseract
        self.prefs["PREFERENCES"]["path_mission"] = self.path_mission
        self.prefs["PREFERENCES"]["dcs_btn_rel_delay_short"] = self.dcs_btn_rel_delay_short
        self.prefs["PREFERENCES"]["dcs_btn_rel_delay_medium"] = self.dcs_btn_rel_delay_medium
        self.prefs["PREFERENCES"]["hotkey_capture"] = self.hotkey_capture
        self.prefs["PREFERENCES"]["hotkey_capture_mode"] = self.hotkey_capture_mode
        self.prefs["PREFERENCES"]["hotkey_enter_profile"] = self.hotkey_enter_profile
        self.prefs["PREFERENCES"]["hotkey_enter_mission"] = self.hotkey_enter_mission
        self.prefs["PREFERENCES"]["hotkey_item_sel_type_toggle"] = self.hotkey_item_sel_type_toggle
        self.prefs["PREFERENCES"]["hotkey_item_sel_advance"] = self.hotkey_item_sel_advance
        self.prefs["PREFERENCES"]["hotkey_dgft_cycle"] = self.hotkey_dgft_cycle
        self.prefs["PREFERENCES"]["airframe_default"] = self.airframe_default
        self.prefs["PREFERENCES"]["av_setup_default"] = self.av_setup_default
        self.prefs["PREFERENCES"]["callsign_default"] = self.callsign_default
        self.prefs["PREFERENCES"]["is_auto_upd_check"] = self.is_auto_upd_check
        self.prefs["PREFERENCES"]["is_tesseract_debug"] = self.is_tesseract_debug
        self.prefs["PREFERENCES"]["is_av_setup_for_unk"] = self.is_av_setup_for_unk
        self.prefs["PREFERENCES"]["is_f10_elev_clamped"] = self.is_f10_elev_clamped
        self.prefs["PREFERENCES"]["is_load_auto_quit"] = self.is_load_auto_quit
        self.prefs["PREFERENCES"]["is_disable_export"] = self.is_disable_export
        self.prefs["PREFERENCES"]["last_profile_sel"] = self.last_profile_sel

        if do_write:
            with open(self.path_ini, "w+") as f:
                self.prefs.write(f)
            logger.info("Preferences persisted and written")
