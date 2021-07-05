'''

mission_package.py: Mission pack installation for DCS Waypoint Editor

See documentation/Mission_Packs.md for further information on the format and expectations
around mission packs.

'''

import os
import tempfile
import zipfile

from shutil import move

from peewee import Value

from src.cf_xml import CombatFliteXML
from src.objects import Profile
from src.logger import get_logger

logger = get_logger(__name__)


# maps internal type for airframe : DCS airframe kneeboard directory name
#
airframe_map = { "warthog" : "A-10C",
                 "harrier" : "AV8BNA",
                 "tomcat" : "F-14B",
                 "viper" : "F-16C_50",
                 "hornet" : "FA-18C_hornet",
                 "mirage" : "M-2000C"
}

# unpack and install a mission package for a given call sign. returns a profile for
# the waypoints associated with the callsign in the mission.
#
def dcswe_install_mpack(mpack_path, mpack_name, airframe, callsign, dcs_path):
    logger.info(f"Installing mission pack for {callsign} ({airframe}) from {mpack_path}")

    profile = None

    flight = (callsign.split("-"))[0]

    try:
        kb_path = f"{dcs_path}\\Kneeboard\\{airframe_map[airframe]}"
    except:
        raise ValueError("Unable to find per-airframe kneeboard path in DCS directory.")
    if not os.path.exists(kb_path):
        raise ("Unable to find per-airframe kneeboard path in DCS directory.")
    logger.info(f"Kneeboards path found at: {kb_path}")

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(mpack_path) as zip_ref:
                zip_ref.extractall(tmp_dir)

            flight_path = None
            mission_top_path = None
            with os.scandir(tmp_dir) as files:
                for entry in files:
                    file = entry.name.lower()
                    if mission_top_path is None and file.endswith(".json") or file.endswith(".xml"):
                        mission_top_path = f"{tmp_dir}\\{entry.name}"
                    if file == flight.lower():
                        flight_path = f"{tmp_dir}\\{flight}"
            if flight_path is None:
                raise ValueError(f"The flight {flight} was not found in the mission package.")

            kb_pages = []
            mission_path = mission_top_path
            with os.scandir(flight_path) as files:
                for entry in files:
                    file = entry.name.lower()
                    if mission_path == mission_top_path and file.endswith(".json") or file.endswith(".xml"):
                        mission_path = f"{flight_path}\\{entry.name}"
                    elif file.endswith(".png") or file.endswith(".jpg"):
                        kb_pages.append(entry.name)

            if mission_path is not None:
                with open(mission_path, "rb") as f:
                    mission_data = f.read()
                mission_str = mission_data.decode("UTF-8")
                if CombatFliteXML.is_xml(str):
                    profile = CombatFliteXML.profile_from_string(mission_str, callsign, "", airframe)
                else:
                    profile = Profile.from_string(mission_str)
                if not profile.has_waypoints:
                    raise ValueError(f"No waypoints found in the mission package for {callsign}.")
                logger.info(f"Created mission profile for {mission_path}")
                profile.profilename = mpack_name
                if profile.aircraft is None:
                    profile.aircraft = airframe
            else:
                logger.info(f"No mission found in package")

            index = 1
            mpack_name_nos = mpack_name.replace(" ", "-")
            for kb_page in sorted(kb_pages):
                _, ext = os.path.splitext(kb_page)
                src_path = f"{flight_path}\\{kb_page}"
                dst_path = f"{kb_path}\\001-{mpack_name_nos}-{index:03d}{ext}"
                logger.info(f"Kneeboard {src_path} --> {dst_path}")
                try:
                    move(src_path, dst_path)
                except:
                    raise ValueError(f"Unable to move kneeboard page '{kb_page}' to {kb_path}.")
                index = index + 1

    except Exception as e:
        raise e

    return profile