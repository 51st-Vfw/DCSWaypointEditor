'''
*
*  cf_xml.py: CombatFlite XML parsing into DCS Waypoint Editor profiles
*
*  See documentation/CF_Integration.md for further details on the expectations DCS Waypoint
*  Editor places on CombatFlite missions that it can import.
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

import re
import xml.etree.ElementTree as xml

from src.db_objects import Profile, Waypoint, MSN
from src.logger import get_logger

from LatLon23 import LatLon, Longitude, Latitude
from typing import Any


logger = get_logger(__name__)


# class to build DCSWE profiles from CombatFlite XML exports.
#
class CombatFliteXML:

    # returns a cleaned up name from a CombatFlite XML element.
    #
    @staticmethod
    def elem_get_name(elem):
        e_nam = elem.find("Name")
        if e_nam is not None:
            return e_nam.text.replace("\n", " ")
        else:
            return ""

    # returns a { LatLon, elev } position tuple from a CombatFlite XML element.
    #
    @staticmethod
    def elem_get_position(elem):
        e_pos = elem.find("Position")
        e_lat = e_pos.find("Latitude")
        e_lon = e_pos.find("Longitude")
        e_alt = e_pos.find("Altitude")
        if e_lat is None or e_lon is None:
            raise ValueError("Failed to find position in XML element")
        if e_alt is None:
            elev = 0.0
        else:
            elev = int(float(e_alt.text) * 3.2808399)
        return LatLon(Latitude(e_lat.text), Longitude(e_lon.text)), elev

    # returns True/False if the element's name matches a regex.
    #
    @staticmethod
    def elem_name_matches(elem, name_regex):
        name = CombatFliteXML.elem_get_name(elem)
        if name != "":
            res = re.match(name_regex, name, flags=re.IGNORECASE)
            if res is not None:
                return True
        return False

    # returns an array with all "Waypoint" elements from the CombatFlite XML whose name
    # matches a regex.
    #
    @staticmethod
    def find_waypoints_named(root, name_regex):
        elem_wp = []
        for elem in root.iter("Waypoint"):
            if CombatFliteXML.elem_name_matches(elem, name_regex):
                elem_wp.append(elem)
        return elem_wp

    # returns an array with all "Object" elements from the CombatFlite XML whose name matches
    # a regex.
    #
    @staticmethod
    def find_objects_named(root, name_regex):
        elem_obj = []
        for elem in root.iter("Object"):
            if CombatFliteXML.elem_name_matches(elem, name_regex):
                elem_obj.append(elem)
        return elem_obj

    # check to see if a string contains a valid XML object.
    #
    @staticmethod
    def is_xml(str):
        try:
            str.index("<?xml version")
            return True
        except:
            return False

    # match a callsign against a DMPI reference point ship list, returning station.
    #
    @staticmethod
    def find_matching_ship(flight, ship, dmpi_name):
        flight = flight.lower()
        ship = ship.lower()

        match = re.match(r"DMPI [\d]+[\s]*(?P<ship_list>.*)", dmpi_name.lower(), flags=re.IGNORECASE)
        if not match:
            return None

        tokens = match.group('ship_list').split(" ")
        if flight == "" or len(match.group('ship_list')) == 0:
            return "8"

        for token in tokens:
            tokens_elem = token.split(":")
            if len(tokens_elem) != 2:
                tokens_elem.append("8")

            tokens_ship = tokens_elem[0].split("-")
            if "*" in tokens_ship[0]:
                if tokens_ship[0][-1].isdigit():
                    regex = r"^" + tokens_ship[0].replace("*", r"[\D]+")
                else:
                    regex = r"^" + tokens_ship[0].replace("*", r"[\D]+[\d]+")
                if re.match(regex, flight):
                    tokens_ship[0] = flight
            if tokens_ship[0] == flight and (len(tokens_ship) == 1 or
                                             tokens_ship[1] == ship):
                return tokens_elem[1]
            elif tokens_ship[0] == flight and len(tokens_ship) == 1:
                return "8"

        return None

    # generate a list of all flights in a CombatFlite XML string by inspecting the waypoint
    # elements
    #
    @staticmethod
    def flight_names_from_xml_string(str):
        try:
            index = str.index("<?xml version")
            str = str[index:]
        except:
            raise ValueError("Data does not contain a vaild XML description")

        try:
            root = xml.fromstring(str)
            flights = []
            for elem in root.iter("Waypoint"):
                match = re.match(r"^(?P<flight>[^-\s]+)", CombatFliteXML.elem_get_name(elem))
                if match and match.group('flight') not in flights:
                    flights.append(match.group('flight'))
        except:
            raise ValueError("Failed to parse CombatFlite XML file")

        flights.sort()
        return flights

    # create and populate a DCSWE profile from an CombatFlite XML string.
    #
    # callsign, if given, should be in the format "<name><number>-<ship>", e.g., "Enfield1-2"
    #
    @staticmethod
    def profile_from_xml_string(str, callsign="", name="", aircraft="viper"):
        logger.info(f"CF XML from string for '{callsign}' in '{aircraft}'")

        match = re.match(r"^(?P<flight>[a-zA-Z]+[\d]+)-(?P<ship>[\d]+)$",
                         callsign, flags=re.IGNORECASE)
        if match and match.group('flight') is not None and match.group('ship') is not None:
            flight = match.group('flight')
            ship = match.group('ship')
        else:
            flight = ""
            ship = ""

        try:
            index = str.index("<?xml version")
            str = str[index:]
        except:
            raise ValueError("Data does not contain a vaild XML description")

        try:
            root = xml.fromstring(str)

            # grab "Waypoint" elements from the XML that match the flight name. these map to
            # WP waypoints in DCS.
            #
            wps = []
            for elem in CombatFliteXML.find_waypoints_named(root, f"^{flight}"):
                name = CombatFliteXML.elem_get_name(elem)
                posn, elev = CombatFliteXML.elem_get_position(elem)
                wp = Waypoint(name=name, sequence=0, position=posn, elevation=elev)
                logger.info(f"{wp}")
                wps.append(wp)
            logger.info(f"CF XML: Built {len(wps)} '{callsign}' WP waypoints")

            # grab "Object" elements from the XML that have a name beginning with "DMPI ".
            # these map to MSN waypoints in DCS.
            #
            # split this into two groups: one for DMPIs associated with a target waypoint
            # (these have names like "DMPI targeted by Colt1") for the flight, and one for
            # DMPIs for DMPI reference points (these have names like "DMPI 1").
            #
            # note that the first group is restricted to the flight, the second has *all*
            # DMPIs.
            #
            dmpi_wypt = []
            dmpi_refp = []
            for elem in CombatFliteXML.find_objects_named(root, f"DMPI "):
                name = CombatFliteXML.elem_get_name(elem)
                match = re.match(r"^DMPI targeted by (?P<flight>[\S]+)",
                                 name, flags=re.IGNORECASE)
                if match and (callsign == "" or flight.lower() == match.group('flight').lower()):
                    dmpi_wypt.append(elem)
                elif not match:
                    dmpi_refp.append(elem)
            logger.info(f"CF XML: got {len(dmpi_wypt)} '{flight}' DMPI waypoints")
            logger.info(f"CF XML: got {len(dmpi_refp)} DMPI reference points")

            # build the list of MSN waypoints from the combination of the waypoint and
            # reference point elements.
            #
            # the reference point elements, through their name, can map a specific DMPI
            # to a specific jet in the flight along with a specific station on the jet.
            # it does this through the DMPI reference point name which should be of the
            # format "DMPI <number> <ship>:<station>"
            #
            msns = []
            for elem_w in dmpi_wypt:
                pos_wypt, elv_wypt = CombatFliteXML.elem_get_position(elem_w)
                for elem_r in dmpi_refp:
                    pos_refp, _ = CombatFliteXML.elem_get_position(elem_r)
                    if pos_wypt.almost_equal(pos_refp, e=0.00001):
                        name = CombatFliteXML.elem_get_name(elem_r)
                        dmpi_stn = CombatFliteXML.find_matching_ship(flight, ship, name)
                        if dmpi_stn is not None:
                            if callsign == "":
                                name = CombatFliteXML.elem_get_name(elem_w)
                            msn = MSN(name=name, station=dmpi_stn,
                                      position=pos_wypt, elevation=elv_wypt)
                            logger.info(f"{msn}")
                            msns.append(msn)
            logger.info(f"CF XML: Built {len(msns)} '{callsign}' MSN waypoints")

            return Profile(name, waypoints=wps+msns, aircraft=aircraft)

        except:
            raise ValueError("Failed to parse CombatFlite XML file")

'''
def test_find_matching_ship():
    print([ 1, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI")])
    print([ 2, "8", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1")])
    print([ 3, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "colt1-1:2")])
    print([ 4, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI colt1-1:2")])
    print([ 5, "6", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 colt1-1:6")])
    print([ 6, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 colt1-2:2")])
    print([ 7, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 colt2-1:2")])
    print([ 8, "7", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 co*1-1:7")])
    print([ 9, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 co*1-2:2")])
    print([10, "4", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 co*1-2:2 co*1-1:4")])
    print([11, "6", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 en*1-2:2 co*1-1:6")])
    print([12, "8", CombatFliteXML.find_matching_ship("", "", "DMPI 1 colt1-1:2")])
    print([13, "8", CombatFliteXML.find_matching_ship("", "", "DMPI 1 colt1-2:2")])
    print([14, "8", CombatFliteXML.find_matching_ship("", "", "DMPI 1 co*1-1:2")])
    print([15, "8", CombatFliteXML.find_matching_ship("", "", "DMPI 1 co*1-2:2")])
    print([16, "2", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 colt1:2")])
    print([16, "N", CombatFliteXML.find_matching_ship("Colt2", "1", "DMPI 1 colt1:2")])
    print([17, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 colt2:2")])
    print([18, "2", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 co*1:2")])
    print([19, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 co*2:2")])
    print([20, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 en*1:2")])
    print([21, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 en*2:2")])
    print([22, "2", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 co*:2")])
    print([23, "3", CombatFliteXML.find_matching_ship("Colt2", "1", "DMPI 1 co*:3")])
    print([24, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 en*:2")])
    print([25, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 en*:2")])
    print([26, "3", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 co*-1:3")])
    print([27, "2", CombatFliteXML.find_matching_ship("Colt2", "1", "DMPI 1 co*-1:2")])
    print([28, "N", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 co*-2:2")])
    print([29, "N", CombatFliteXML.find_matching_ship("Colt2", "1", "DMPI 1 co*-2:2")])
    print([30, "8", CombatFliteXML.find_matching_ship("Colt1", "1", "DMPI 1 colt1-1")])
'''