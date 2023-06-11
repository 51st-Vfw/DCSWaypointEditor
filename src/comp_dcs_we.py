'''
*
*  comp_dcs_WE.py: DCS Waypoint Editor component version management and update support
*
*  See documentation/CF_Integration.md for further details on the expectations DCS Waypoint
*  Editor places on CombatFlite missions that it can import.
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

import urllib.request
import webbrowser

from src.logger import get_logger


DCS_WE_VERSION = "v1.8.0-51stVFW"

logger = get_logger(__name__)


# return version of latest DCS waypoint editor, None if unknown.
#
# latest version is pulled from master branch on github.
#
def dcs_we_vers_latest():
    version_url = "https://raw.githubusercontent.com/51st-Vfw/DCSWaypointEditor/master/release_version.txt"

    try:
        with urllib.request.urlopen(version_url) as response:
            if response.code == 200:
                html = response.read()
            else:
                return None
    except (urllib.error.HTTPError, urllib.error.URLError):
        return None

    return html.decode("utf-8")

# return installed version of current DCS waypoint editor.
#
def dcs_we_vers_install():
    return DCS_WE_VERSION

# check if DCS waypoint editor is up-to-date.
#
def dcs_we_is_current():
    return True if dcs_we_vers_latest() == DCS_WE_VERSION else False

# install DCS waypoint editor.
#
# opens a web browser on releases section of the DCSWE github. user can figure the rest out....
#
def dcs_we_install():
    try:
        logger.debug("redirecting to DCSWE releases on GitHub...")
        webbrowser.open("https://github.com/51st-Vfw/DCSWaypointEditor/releases")
        vers = dcs_we_vers_latest()
    except:
        vers = None
    return vers
