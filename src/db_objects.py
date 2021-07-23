'''
*
*  db_objects.py: DCS Waypoint Editor profile database objects
*
*  Copyright (C) 2020 Santi871
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

import json

from dataclasses import dataclass, asdict
from LatLon23 import LatLon, Longitude, Latitude
from os import walk
from peewee import IntegrityError
from typing import Any

from src.db_models import ProfileModel, WaypointModel, SequenceModel, AvionicsSetupModel
from src.db_models import db
from src.logger import get_logger


default_bases = dict()

logger = get_logger(__name__)


def base_data_load(basedata, basedict):
    waypoints_list = basedata.get("waypoints")

    if type(waypoints_list) == list:
        basedata = {i: wp for i, wp in enumerate(waypoints_list)}

    for _, base in basedata.items():
        name = base.get('name')

        if name not in ("Stennis", "Kuznetsov", "Kuznetsov North", "Kuznetsov South"):
            lat = base.get("latitude") or base.get(
                'locationDetails').get('lat')
            lon = base.get("longitude") or base.get(
                'locationDetails').get('lon')
            elev = base.get("elevation")
            if elev is None:
                elev = base.get('locationDetails').get('altitude')
            position = LatLon(Latitude(degree=lat), Longitude(degree=lon))
            basedict[name] = Waypoint(position=position, name=name, elevation=elev)


def generate_default_bases():
    for _, _, files in walk(".\\data"):
        for filename in files:
            if ".json" in filename:
                with open(".\\data\\" + filename, "r") as f:
                    try:
                        base_data_load(json.load(f), default_bases)
                        logger.info(f"Default base data built succesfully from file: {filename}")
                    except AttributeError:
                        logger.warning(
                            f"Failed to build default base data from file: {filename}", exc_info=True)


@dataclass
class Waypoint:
    position: Any
    number: int = 0
    elevation: int = 0
    name: str = ""
    sequence: int = 0
    wp_type: str = "WP"
    latitude: float = None
    longitude: float = None

    def __post_init__(self):
        if type(self.position) == str:
            base = default_bases.get(self.position)

            if base is not None:
                self.elevation = base.elev
                self.name = self.position
                self.position = base.position
            else:
                raise ValueError("Base name not found in default bases list")

        elif not type(self.position) == LatLon:
            raise ValueError("Waypoint position must be a LatLon object or base name string")

        self.latitude = self.position.lat.decimal_degree
        self.longitude = self.position.lon.decimal_degree

    def __str__(self):
        strrep = f"{self.wp_type}{self.number}"
        if self.wp_type == "WP" and self.sequence:
            strrep += f" | SEQ{self.sequence}"
        if self.name:
            strrep += f" | {self.name}"
        return strrep

    @property
    def as_dict(self):
        d = asdict(self)
        del d["position"]
        return d

    @staticmethod
    def to_object(dict):
        return Waypoint(LatLon(Latitude(dict.get('latitude')), Longitude(dict.get('longitude'))),
                        elevation=dict.get('elevation'), name=dict.get('name'),
                        sequence=dict.get('sequence'), wp_type=dict.get('wp_type'))


@dataclass
class MSN(Waypoint):
    station: int = 0

    def __post_init__(self):
        super().__post_init__()
        self.wp_type = "MSN"
        if not self.station:
            raise ValueError("MSN station not defined")

    def __str__(self):
        strrep = f"MSN{self.number} | STA{self.station}"
        if self.name:
            strrep += f" | {self.name}"
        return strrep

    @staticmethod
    def to_object(dict):
        return MSN(LatLon(Latitude(dict.get('latitude')), Longitude(dict.get('longitude'))),
                   elevation=dict.get('elevation'), name=dict.get('name'),
                   sequence=dict.get('sequence'), wp_type=dict.get('wp_type'),
                   station=dict.get('station'))


class Profile:
    def __init__(self, profilename, waypoints=None, aircraft="viper", av_setup_name=None):
        self.profilename = profilename
        self.aircraft = aircraft
        self.av_setup_name = av_setup_name

        if waypoints is None:
            self.waypoints = list()
        else:
            self.waypoints = waypoints
            self.update_waypoint_numbers()

    def __str__(self):
        return json.dumps(self.to_dict())

    def update_sequences(self):
        sequences = set()
        for waypoint in self.waypoints:
            if type(waypoint) == Waypoint and waypoint.sequence:
                sequences.add(waypoint.sequence)
        sequences = list(sequences)
        sequences.sort()
        return sequences

    @property
    def has_waypoints(self):
        return len(self.waypoints) > 0

    @property
    def sequences(self):
        return self.update_sequences()

    @property
    def waypoints_as_list(self):
        return [wp for wp in self.waypoints if type(wp) == Waypoint]

    @property
    def all_waypoints_as_list(self):
        return [wp for wp in self.waypoints if not isinstance(wp, MSN)]

    @property
    def msns_as_list(self):
        return [wp for wp in self.waypoints if isinstance(wp, MSN)]

    @property
    def stations_dict(self):
        stations = dict()
        for mission in self.msns_as_list:
            station_msn_list = stations.get(mission.station, list())
            station_msn_list.append(mission)
            stations[mission.station] = station_msn_list
        return stations

    @property
    def waypoints_dict(self):
        wps_dict = dict()
        for wp in self.waypoints_as_list:
            wps_list = wps_dict.get(wp.wp_type, list())
            wps_list.append(wp)
            wps_dict[wp.wp_type] = wps_list
        return wps_dict

    @property
    def sequences_dict(self):
        d = dict()
        for sequence_identifier in self.sequences:
            for i, wp in enumerate(self.waypoints_as_list):
                if wp.sequence == sequence_identifier:
                    wp_list = d.get(sequence_identifier, list())
                    wp_list.append(i+1)
                    d[sequence_identifier] = wp_list

        return d

    @property
    def av_setup_dict(self):
        if self.av_setup_name is not None:
            try:
                avs_dict = dict()
                setup = AvionicsSetupModel.get(AvionicsSetupModel.name == self.av_setup_name)
                if setup.tacan_yard is not None:
                    avs_dict['tacan_yard'] = setup.tacan_yard
                if setup.f16_mfd_setup_nav is not None:
                    avs_dict['f16_mfd_setup_nav'] = setup.f16_mfd_setup_nav
                if setup.f16_mfd_setup_air is not None:
                    avs_dict['f16_mfd_setup_air'] = setup.f16_mfd_setup_air
                if setup.f16_mfd_setup_gnd is not None:
                    avs_dict['f16_mfd_setup_gnd'] = setup.f16_mfd_setup_gnd
                if setup.f16_mfd_setup_dog is not None:
                    avs_dict['f16_mfd_setup_dog'] = setup.f16_mfd_setup_dog
                return avs_dict
            except:
                pass
        return None

    def waypoints_of_type(self, wp_type):
        return [wp for wp in self.waypoints if wp.wp_type == wp_type]

    def get_sequence(self, identifier):
        return self.sequences_dict.get(identifier, list())

    def to_dict(self):
        return dict(
            waypoints=[waypoint.as_dict for waypoint in self.waypoints],
            name=self.profilename,
            aircraft=self.aircraft,
            av_setup_name=self.av_setup_name
        )

    def update_waypoint_numbers(self):
        for _, station_msn_list in self.stations_dict.items():
            for i, mission in enumerate(station_msn_list, 1):
                mission.number = i

        for _, waypoint_list in self.waypoints_dict.items():
            for i, waypoint in enumerate(waypoint_list, 1):
                waypoint.number = i

    def to_readable_string(self):
        readable_string = "Waypoints:\n\n"
        for wp in self.waypoints:
            if wp.wp_type != "MSN":
                position = LatLon(Latitude(wp.latitude),
                                  Longitude(wp.longitude)).to_string("d%°%m%'%S%\"%H")
                readable_string += str(wp)
                readable_string += f": {position[0]} {position[1]} | {wp.elevation}ft\n"

        readable_string += "\nPreplanned Missions:\n\n"

        for wp in sorted(self.waypoints_of_type("MSN"), key=lambda waypoint: waypoint.station):
            if wp.wp_type == "MSN":
                position = LatLon(Latitude(wp.latitude),
                                  Longitude(wp.longitude)).to_string("d%°%m%'%S%\"%H")
                readable_string += str(wp)
                readable_string += f": {position[0]} {position[1]} | {wp.elevation}ft\n"

        readable_string += f"\nAvionics Setup:\n\n{self.av_setup_name}\n"

        return readable_string

    @staticmethod
    def from_string(profile_string):
        profile_data = json.loads(profile_string)
        try:
            profile_name = profile_data["name"]
            waypoints = profile_data["waypoints"]
            wps = [Waypoint.to_object(w) for w in waypoints if w['wp_type'] != 'MSN']
            msns = [MSN.to_object(w) for w in waypoints if w['wp_type'] == 'MSN']
            aircraft = profile_data["aircraft"]
            av_setup_name = profile_data["av_setup_name"]
            profile = Profile(profile_name, waypoints=wps+msns, aircraft=aircraft,
                              av_setup_name=av_setup_name)
            if profile.profilename:
                profile.save()
            return profile
        except Exception as e:
            logger.error(e)
            raise ValueError("Failed to load profile from data")

    def save(self, profilename=None):
        delete_list = list()
        if profilename is not None:
            self.profilename = profilename

        try:
            with db.atomic():
                profile = ProfileModel.create(name=self.profilename, aircraft=self.aircraft)
        except IntegrityError:
            profile = ProfileModel.get(ProfileModel.name == self.profilename)
        profile.aircraft = self.aircraft
        profile.av_setup_name = self.av_setup_name

        for waypoint in profile.waypoints:
            delete_list.append(waypoint)

        for sequence in profile.sequences:
            delete_list.append(sequence)

        sequences_db_instances = dict()
        for sequencenumber in self.sequences:
            sequence_db_instance = SequenceModel.create(
                identifier=sequencenumber,
                profile=profile
            )
            sequences_db_instances[sequencenumber] = sequence_db_instance

        for waypoint in self.waypoints:
            if not isinstance(waypoint, MSN):
                sequence = sequences_db_instances.get(waypoint.sequence)
                WaypointModel.create(
                    name=waypoint.name,
                    latitude=waypoint.position.lat.decimal_degree,
                    longitude=waypoint.position.lon.decimal_degree,
                    elevation=waypoint.elevation,
                    profile=profile,
                    sequence=sequence,
                    wp_type=waypoint.wp_type
                )
            else:
                WaypointModel.create(
                    name=waypoint.name,
                    latitude=waypoint.position.lat.decimal_degree,
                    longitude=waypoint.position.lon.decimal_degree,
                    elevation=waypoint.elevation,
                    profile=profile,
                    wp_type=waypoint.wp_type,
                    station=waypoint.station
                )

        for instance in delete_list:
            instance.delete_instance()
        profile.save()

    @staticmethod
    def load(profile_name):
        profile = ProfileModel.get(ProfileModel.name == profile_name)
        aircraft = profile.aircraft
        av_setup_name = profile.av_setup_name

        wps = list()
        for waypoint in profile.waypoints:
            try:
                sequence = waypoint.sequence.identifier
            except AttributeError:
                sequence = 0

            if waypoint.wp_type != "MSN":
                wp = Waypoint(LatLon(Latitude(waypoint.latitude), Longitude(waypoint.longitude)),
                              elevation=waypoint.elevation, name=waypoint.name, sequence=sequence,
                              wp_type=waypoint.wp_type)
            else:
                wp = MSN(LatLon(Latitude(waypoint.latitude), Longitude(waypoint.longitude)),
                         elevation=waypoint.elevation, name=waypoint.name, sequence=sequence,
                         wp_type=waypoint.wp_type, station=waypoint.station)
            wps.append(wp)

        profile = Profile(profile_name, waypoints=wps, aircraft=aircraft, av_setup_name=av_setup_name)
        profile.update_waypoint_numbers()
        logger.debug(f"Fetched {profile_name} from DB, with {len(wps)} waypoints")
        return profile

    @staticmethod
    def delete(profile_name):
        profile = ProfileModel.get(name=profile_name)

        for waypoint in profile.waypoints:
            waypoint.delete_instance()

        profile.delete_instance(recursive=True)
