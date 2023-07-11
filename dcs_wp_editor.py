'''
*
*  dcs_wp_editor.py: DCS waypoint editor
*
*  Copyright (C) 2020 Santi871
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

import logging
import os
import traceback

from pathlib import Path

from src.comp_dcs_bios import dcs_bios_vers_install, dcs_bios_vers_latest, dcs_bios_install
from src.comp_dcs_bios import dcs_bios_is_dcswe_config_installed, dcs_bios_update_config
from src.comp_dcs_we import dcs_we_vers_install, dcs_we_vers_latest, dcs_we_install
from src.db_objects import generate_default_bases
from src.gui_util import gui_update_request, gui_new_install_request, gui_exception
from src.gui_util import gui_update_dcsbios_cfg_request
from src.logger import get_logger, trim_logfile
from src.prefs import Preferences
from src.prefs_gui import PreferencesGUI
from src.wp_editor import WaypointEditor
from src.wp_editor_gui import WaypointEditorGUI


# determine where to keep dcswe files (profile database, preferences, etc.). ideally, we
# do this in documents; if not, fall back to the application directory. on a new install,
# open up the prefs ui to give the user a chance to set things up.
#
# returns path to app data, None if setup fails
#
def setup_app_data_environment():
    data_path = Preferences.locate_dcswe_prefs()
    if data_path is None:
        data_path = f"{Path.home()}\\Documents\\DCSWE" + '\\'
        if not os.path.exists(data_path):
            try:
                if not gui_new_install_request(data_path):
                    data_path = ".\\"
                else:
                    os.mkdir(data_path)
            except:
                data_path = ".\\"

        prefs = Preferences(data_path=data_path)

        prefs_gui = PreferencesGUI(prefs)
        if not prefs_gui.run():
            data_path = None

    return data_path

# main.
#
def main(logger, data_path):
    prefs = Preferences(data_path=data_path)
    vers_sw_cur = dcs_we_vers_install()
    vers_sw_latest = dcs_we_vers_latest()

    logger.info(f"Preferences path: {prefs.path_ini}")
    prefs.prefs_to_logger(logger)
    logger.info(f"Profile dbase path: {prefs.path_profile_db}")
    logger.info(f"SW version (current): {vers_sw_cur}")
    logger.info(f"SW version (latest): {vers_sw_latest}")

    # launch the main ui loop if user doesn't want to update dcswe (or it's up-to-date).
    # before hitting the main loop, check for a dcsbios update.
    #
    sw_install_fn = lambda: dcs_we_install()
    if not prefs.is_auto_upd_check_bool or \
       not gui_update_request("DCS Waypoint Editor", vers_sw_cur, vers_sw_latest, sw_install_fn):
        logger.info("Setup complete, starting waypoint editor")

        generate_default_bases()

        vers_dbios_cur = dcs_bios_vers_install(prefs.path_dcs)
        vers_dbios_latest = dcs_bios_vers_latest()
        db_install_fn = lambda: dcs_bios_install(prefs.path_dcs)
        if (prefs.is_auto_upd_check_bool and
            gui_update_request("DCS-BIOS", vers_dbios_cur, vers_dbios_latest, db_install_fn)):
            vers_dbios_cur = dcs_bios_vers_install(prefs.path_dcs)

        cfg_install_fn = lambda: dcs_bios_update_config(prefs.path_dcs)
        if not dcs_bios_is_dcswe_config_installed(prefs.path_dcs):
            gui_update_dcsbios_cfg_request(cfg_install_fn)

        editor = WaypointEditor(prefs)

        gui = WaypointEditorGUI(editor, vers_sw_cur, vers_dbios_cur)

        try:
            gui.run()
        except Exception as e:
            gui.close()
            raise e

if __name__ == "__main__":
    data_path = setup_app_data_environment()

    log_header = "============ Launching DCSWE ============"

    trim_logfile(log_header)
    logger = get_logger("dcswe")
    logger.info(log_header)

    if data_path is not None:
        try:
            main(logger, data_path)
        except Exception as e:
            logger.error("Exception occurred", exc_info=True)
            logging.shutdown()
            gui_exception(traceback.format_exc())
            raise e

    logger.info("Exiting")
