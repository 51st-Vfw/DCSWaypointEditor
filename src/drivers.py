'''
*
*  drivers.py: Airframe-specific interfaces to avionics
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

import types
import keyboard
import re
import socket
import queue

from time import sleep


class DriverException(Exception):
    pass


def latlon_tostring(latlong, decimal_minutes_mode=False, easting_zfill=2, zfill_minutes=2, one_digit_seconds=False, precision=4):

    if not decimal_minutes_mode:
        lat_deg = str(abs(round(latlong.lat.degree)))
        lat_min = str(abs(round(latlong.lat.minute))).zfill(zfill_minutes)
        lat_sec = abs(latlong.lat.second)

        lat_sec_int, lat_sec_dec = divmod(lat_sec, 1)

        lat_sec = str(int(lat_sec_int)).zfill(2)

        if lat_sec_dec:
            lat_sec += "." + str(round(lat_sec_dec, 2))[2:4]

        lon_deg = str(abs(round(latlong.lon.degree))).zfill(easting_zfill)
        lon_min = str(abs(round(latlong.lon.minute))).zfill(zfill_minutes)
        lon_sec = abs(latlong.lon.second)

        lon_sec_int, lon_sec_dec = divmod(lon_sec, 1)

        lon_sec = str(int(lon_sec_int)).zfill(2)

        if lon_sec_dec:
            lon_sec += "." + str(round(lon_sec_dec, 2))[2:4]

        if one_digit_seconds:
            lat_sec = str(round(float(lat_sec)) // 10)
            lon_sec = str(round(float(lon_sec)) // 10)

        return lat_deg + lat_min + lat_sec, lon_deg + lon_min + lon_sec
    else:
        lat_deg = str(abs(round(latlong.lat.degree)))
        lat_min = str(format(latlong.lat.decimal_minute, str(precision/10)+"f"))

        lat_min_split = lat_min.split(".")
        lat_min_split[0] = lat_min_split[0].zfill(zfill_minutes)
        lat_min = ".".join(lat_min_split)

        lon_deg = str(abs(round(latlong.lon.degree))).zfill(easting_zfill)
        lon_min = str(format(latlong.lon.decimal_minute, str(precision/10)+"f"))

        lon_min_split = lon_min.split(".")
        lon_min_split[0] = lon_min_split[0].zfill(zfill_minutes)
        lon_min = ".".join(lon_min_split)

        return lat_deg + lat_min, lon_deg + lon_min

'''
***********************************************************************************************************************

Driver Base Class

***********************************************************************************************************************
'''

class Driver:
    def __init__(self, logger, prefs, host="127.0.0.1", port=7778):
        self.logger = logger
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host, self.port = host, port
        self.prefs = prefs
        self.limits = dict()

        self.short_delay = float(self.prefs.dcs_btn_rel_delay_short)
        self.medium_delay = float(self.prefs.dcs_btn_rel_delay_medium)
        self.long_delay = float(2.00 * self.medium_delay)

        self.bkgnd_prog_cur = 0
        self.bkgnd_prog_step = 0

    def keyboard_key_with_delay(self, key, delay_after=None):
        if delay_after is None:
            delay_after = self.medium_delay
        keyboard.send(key)
        sleep(delay_after)

    def press_with_delay(self, key, delay_after=None, delay_release=None, raw=False):
        if not key:
            return False

        if delay_after is None:
            delay_after = self.short_delay

        if delay_release is None:
            delay_release = self.short_delay

        encoded_str = key.replace("OSB", "OS").encode("utf-8")

        # TODO get rid of the OSB -> OS replacement
        if not raw:
            sent = self.s.sendto(f"{key} 1\n".replace("OSB", "OS").encode(
                "utf-8"), (self.host, self.port))
            sleep(delay_release)

            self.s.sendto(f"{key} 0\n".replace("OSB", "OS").encode(
                "utf-8"), (self.host, self.port))
            strlen = len(encoded_str) + 3
        else:
            sent = self.s.sendto(f"{key}\n".encode("utf-8"), (self.host, self.port))
            strlen = len(encoded_str) + 1

        sleep(delay_after)
        return sent == strlen

    def validate_waypoint(self, waypoint):
        try:
            return self.limits[waypoint.wp_type] is None or waypoint.number <= self.limits[waypoint.wp_type]
        except KeyError:
            return False

    def validate_waypoints(self, waypoints):
        for waypoint in waypoints:
            if not self.validate_waypoint(waypoint):
                waypoints.remove(waypoint)
        return sorted(waypoints, key=lambda wp: wp.wp_type)

    # bkgnd_advance will raise an "Operation Cancelled" exception if the operation is cancelled
    #
    def bkgnd_advance(self, command_q, progress_q, is_done=False):
        try:
            if command_q is not None and command_q.get(False) == "CANCEL":
                raise Exception("Operation Cancelled")
        except queue.Empty:
            pass

        if progress_q is not None and is_done:
            progress_q.put(100)
            progress_q.put("DONE")
        elif progress_q is not None:
            self.bkgnd_prog_cur = self.bkgnd_prog_cur + self.bkgnd_prog_step
            progress_q.put(self.bkgnd_prog_cur)
            if self.bkgnd_prog_cur > 100:
                self.bkgnd_prog_cur = 100
    
    def stop(self):
        self.s.close()

'''
***********************************************************************************************************************

F/A-18C Driver Class

***********************************************************************************************************************
'''

class HornetDriver(Driver):
    def __init__(self, logger, config):
        super().__init__(logger, config)
        self.limits = dict(WP=None, MSN=6)

    def ufc(self, num, delay_after=None, delay_release=None):
        key = f"UFC_{num}"
        self.press_with_delay(key, delay_after=delay_after,
                              delay_release=delay_release)

    def lmdi(self, pb, delay_after=None, delay_release=None):
        key = f"LEFT_DDI_PB_{pb.zfill(2)}"
        self.press_with_delay(key, delay_after=delay_after,
                              delay_release=delay_release)

    def ampcd(self, pb, delay_after=None, delay_release=None):
        key = f"AMPCD_PB_{pb.zfill(2)}"
        self.press_with_delay(key, delay_after=delay_after,
                              delay_release=delay_release)

    def ensure_decimal(self, number):
        if str(number).find(".") == -1:
            number = number + ".0"
        return number

    def enter_number(self, number, two_enters=False):
        for num in str(number):
            if num in "0123456789":
                self.ufc(num)
            elif num == ".":
                break

        self.ufc("ENT", delay_release=self.long_delay, delay_after=self.medium_delay)

        i = str(number).find(".")
        if two_enters and i > 0:
            for num in str(number)[i + 1:]:
                self.ufc(num)

            self.ufc("ENT", delay_release=self.long_delay, delay_after=self.medium_delay)

    def enter_coords(self, latlong, elev, pp, decimal_minutes_mode=False):
        lat_str, lon_str = latlon_tostring(latlong, decimal_minutes_mode=decimal_minutes_mode)

        # lat/lon without decimal can confuse enter_number, avoid that situation...
        #
        lat_str = self.ensure_decimal(lat_str)
        lon_str = self.ensure_decimal(lon_str)

        if not pp:
            self.logger.info(f"Entering coords string (W): {lat_str}, {lon_str}")

            if latlong.lat.degree > 0:
                self.ufc("2", delay_release=self.medium_delay)
            else:
                self.ufc("8", delay_release=self.medium_delay)
            self.enter_number(lat_str, two_enters=True)
            sleep(0.5)

            if latlong.lon.degree > 0:
                self.ufc("6", delay_release=self.medium_delay)
            else:
                self.ufc("4", delay_release=self.medium_delay)
            self.enter_number(lon_str, two_enters=True)
            sleep(0.5)

            # For non-pre-planned waypoints skip elevations less than 0 (effectively
            # clamping them to 0). For navagation <0 does not make sense.
            # Hornet avionics do not seem to allow WPT elevations < -2000'
            #
            self.ufc("OSB3")
            self.ufc("OSB1")
            if elev < 0:
                elev = -max(elev, -2000)
                self.ufc("0", delay_release=self.medium_delay)
            self.enter_number(elev)

        else:
            self.logger.info(f"Entering coords string (M): {lat_str}, {lon_str}")

            self.ufc("OSB1")
            if latlong.lat.degree > 0:
                self.ufc("2", delay_release=self.medium_delay)
            else:
                self.ufc("8", delay_release=self.medium_delay)
            self.enter_number(lat_str, two_enters=True)

            self.ufc("OSB3")

            if latlong.lon.degree > 0:
                self.ufc("6", delay_release=self.medium_delay)
            else:
                self.ufc("4", delay_release=self.medium_delay)

            self.enter_number(lon_str, two_enters=True)

            self.lmdi("14")
            self.lmdi("14")

            # For pre-planned waypoints (which are targets), allow elevations less than 0.
            # Hornet avionics do not seem to allow MSN elevations < -328'
            #
            self.ufc("OSB4")
            self.ufc("OSB3")
            if elev < 0:
                elev = -max(elev, -328)
                self.ufc("0", delay_release=self.medium_delay)
            self.enter_number(elev)

    def count_steps_enter_wypts(self, wps, sequences):
        count = 0
        if wps:
            count = len(wps)
            for _, waypointslist in sequences.items():
                count = count + len(waypointslist)
        return count

    def enter_waypoints(self, wps, sequences, command_q=None, progress_q=None):
        if not wps:
            return

        canceled = False

        self.ampcd("10")
        self.ampcd("19")
        self.ufc("CLR")
        self.ufc("CLR")

        for i, wp in enumerate(wps):
            self.bkgnd_advance(command_q, progress_q)

            if not wp.name:
                self.logger.info(f"Entering waypoint {i+1}")
            else:
                self.logger.info(f"Entering waypoint {i+1} - {wp.name}")

            self.ampcd("12")
            self.ampcd("5")
            self.ufc("OSB1")
            self.enter_coords(wp.position, wp.elevation, pp=False, decimal_minutes_mode=True)
            self.ufc("CLR")

        for sequencenumber, waypointslist in sequences.items():
            if canceled:
                break

            if sequencenumber != 1:
                self.ampcd("15")
                self.ampcd("15")
            else:
                waypointslist = [0] + waypointslist

            self.ampcd("1")

            for waypoint in waypointslist:
                self.bkgnd_advance(command_q, progress_q)

                self.ufc("OSB4")
                self.enter_number(waypoint)

        self.ufc("CLR")
        self.ufc("CLR")
        self.ufc("CLR")
        self.ampcd("19")
        self.ampcd("10")

    def enter_pp_msn(self, msn, n):
        if msn.name:
            self.logger.info(f"Entering PP mission {n} - {msn.name}")
        else:
            self.logger.info(f"Entering PP mission {n}")

        if n > 1:
            self.lmdi(f"{n + 5}")
        self.lmdi("14")
        self.ufc("OSB3")

        self.enter_coords(msn.position, msn.elevation, pp=True)

        self.ufc("CLR")
        self.ufc("CLR")

    def enter_missions(self, missions, command_q=None, progress_q=None):
        def stations_order(x):
            if x == 8:
                return 0
            elif x == 7:
                return 2
            elif x == 3:
                return 3
            elif x == 2:
                return 1

        sorted_stations = list()
        stations = dict()
        for mission in missions:
            station_msn_list = stations.get(mission.station, list())
            station_msn_list.append(mission)
            stations[mission.station] = station_msn_list

        for k in sorted(stations, key=stations_order):
            sorted_stations.append(stations[k])

        self.lmdi("19")
        self.lmdi("4")

        canceled = False
        for msns in sorted_stations:
            if not msns:
                return

            n = 1
            for msn in msns:
                self.bkgnd_advance(command_q, progress_q)

                self.enter_pp_msn(msn, n)
                n += 1

            self.lmdi("13")

    def enter_all(self, profile, command_q=None, progress_q=None):
        missions = self.validate_waypoints(profile.msns_as_list)
        waypoints = self.validate_waypoints(profile.waypoints_as_list)

        steps = self.count_steps_enter_wypts(waypoints, profile.sequences_dict) + len(missions)

        self.bkgnd_prog_step = (1.0 / (steps + 2)) * 100.0
        self.bkgnd_prog_cur = 0

        try:
            self.enter_missions(missions, command_q=command_q, progress_q=progress_q)
            self.bkgnd_advance(command_q, progress_q)
            sleep(1)
            self.enter_waypoints(waypoints, profile.sequences_dict, command_q=command_q,
                                progress_q=progress_q)
            self.bkgnd_advance(command_q, progress_q, is_done=True)
        except Exception as e:
            self.logger.debug(f"Exception raised: {e}")

'''
***********************************************************************************************************************

AV-8B Driver Class

***********************************************************************************************************************
'''

class HarrierDriver(Driver):
    def __init__(self, logger, config):
        super().__init__(logger, config)
        self.limits = dict(WP=None)

    def ufc(self, num, delay_after=None, delay_release=None):
        if num not in ("ENT", "CLR"):
            key = f"UFC_B{num}"
        elif num == "ENT":
            key = "UFC_ENTER"
        elif num == "CLR":
            key = "UFC_CLEAR"
        else:
            key = f"UFC_{num}"
        self.press_with_delay(key, delay_after=delay_after,
                              delay_release=delay_release)

    def odu(self, num, delay_after=None, delay_release=None):
        key = f"ODU_OPT{num}"
        self.press_with_delay(key, delay_after=delay_after,
                              delay_release=delay_release)

    def lmpcd(self, pb, delay_after=None, delay_release=None):
        key = f"MPCD_L_{pb}"
        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)

    def enter_number(self, number, two_enters=False):
        for num in str(number):
            if num in "0123456789":
                self.ufc(num)
            elif num == ".":
                break

        self.ufc("ENT", delay_release=self.medium_delay)

        i = str(number).find(".")

        if two_enters:
            if i > 0:
                for num in str(number)[str(number).find(".") + 1:]:
                    if num in "0123456789":
                        self.ufc(num)

            self.ufc("ENT", delay_release=self.medium_delay)

    def enter_coords(self, latlong, elev):
        lat_str, lon_str = latlon_tostring(latlong, decimal_minutes_mode=False, easting_zfill=3)
        self.logger.info(f"Entering coords string: {lat_str}, {lon_str}")

        if latlong.lat.degree > 0:
            self.ufc("2", delay_release=self.medium_delay)
        else:
            self.ufc("8", delay_release=self.medium_delay)
        self.enter_number(lat_str)

        if latlong.lon.degree > 0:
            self.ufc("6", delay_release=self.medium_delay)
        else:
            self.ufc("4", delay_release=self.medium_delay)

        self.enter_number(lon_str)

        if elev:
            self.odu("3")
            #
            # TODO: Check negative elevation support, for now clamp.
            #
            if elev < 0:
                elev = 0
            self.enter_number(elev)

    def enter_waypoints(self, wps, command_q=None, progress_q=None):
        self.lmpcd("2")

        for wp in wps:
            self.bkgnd_advance(command_q, progress_q)

            self.ufc("7")
            self.ufc("7")
            self.ufc("ENT")
            self.odu("2")
            self.enter_coords(wp.position, wp.elevation)
            self.odu("1")

        self.lmpcd("2")

    def enter_all(self, profile, command_q=None, progress_q=None):
        waypoints = self.validate_waypoints(profile.all_waypoints_as_list)

        self.bkgnd_prog_step = (1.0 / (len(waypoints) + 1)) * 100.0
        self.bkgnd_prog_cur = 0

        try:
            self.enter_waypoints(waypoints, command_q=command_q, progress_q=progress_q)
            self.bkgnd_advance(command_q, progress_q, is_done=True)
        except Exception as e:
            self.logger.debug(f"Exception raised: {e}")

'''
***********************************************************************************************************************

M-2000C Driver Class

***********************************************************************************************************************
'''

class MirageDriver(Driver):
    def __init__(self, logger, config):
        super().__init__(logger, config)
        self.limits = dict(WP=9)

    def pcn(self, num, delay_after=None, delay_release=None):
        if num in ("ENTER", "CLR"):
            key = f"INS_{num}_BTN"
        elif num == "PREP":
            key = "INS_PREP_SW"
        else:
            key = f"INS_BTN_{num}"

        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)

    def enter_number(self, number):
        for num in str(number):
            if num in "0123456789":
                self.pcn(num)
        self.pcn("ENTER")

    def enter_coords(self, latlong):
        lat_str, lon_str = latlon_tostring(latlong, decimal_minutes_mode=True, easting_zfill=3)
        self.logger.info(f"Entering coords string: {lat_str[:-2]}, {lon_str[:-2]}")

        self.pcn("1")
        if latlong.lat.degree > 0:
            self.pcn("2", delay_release=self.medium_delay)
        else:
            self.pcn("8", delay_release=self.medium_delay)
        self.enter_number(lat_str[:-2])

        self.pcn("3")

        if latlong.lon.degree > 0:
            self.pcn("6", delay_release=self.medium_delay)
        else:
            self.pcn("4", delay_release=self.medium_delay)
        self.enter_number(lon_str[:-2])

    def enter_waypoints(self, wps, command_q=None, progress_q=None):
        for i, wp in enumerate(wps, 1):
            self.bkgnd_advance(command_q, progress_q)

            self.pcn("PREP")
            self.pcn("0")
            self.pcn(str(i))
            self.enter_coords(wp.position)
            self.pcn("ENTER")

    def enter_all(self, profile, command_q=None, progress_q=None):
        waypoints = self.validate_waypoints(profile.all_waypoints_as_list)

        self.bkgnd_prog_step = (1.0 / (len(waypoints) + 1)) * 100.0
        self.bkgnd_prog_cur = 0

        try:
            self.enter_waypoints(waypoints, command_q=command_q, progress_q=progress_q)
            self.bkgnd_advance(command_q, progress_q, is_done=True)
        except Exception as e:
            self.logger.debug(f"Exception raised: {e}")

'''
***********************************************************************************************************************

F-14A/B Driver Class

***********************************************************************************************************************
'''

class TomcatDriver(Driver):
    def __init__(self, logger, config):
        super().__init__(logger, config)
        self.limits = dict(WP=3, FP=1, IP=1, ST=1, HA=1, DP=1, HB=1)

    def cap(self, num, delay_after=None, delay_release=None):
        raw = False
        cap_key_names = {
            "0": "RIO_CAP_BRG_",
            "1": "RIO_CAP_LAT_",
            "2": "RIO_CAP_NBR_",
            "3": "RIO_CAP_SPD_",
            "4": "RIO_CAP_ALT_",
            "5": "RIO_CAP_RNG_",
            "6": "RIO_CAP_LONG_",
            "8": "RIO_CAP_HDG_",
        }

        if num == "TAC":
            key = "RIO_CAP_CATRGORY 3"
            raw = True
        else:
            key = f"{cap_key_names.get(num, 'RIO_CAP_')}{num}"
        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release, raw=raw)

    def enter_number(self, number):
        for num in str(number):
            if num in "0123456789":
                self.cap(num)
        self.cap("ENTER")

    def enter_coords(self, latlong, elev):
        lat_str, lon_str = latlon_tostring(latlong, one_digit_seconds=True)
        self.logger.info(f"Entering coords string: {lat_str}, {lon_str}")

        self.cap("1")
        if latlong.lat.degree > 0:
            self.cap("NE", delay_release=self.medium_delay)
        else:
            self.cap("SW", delay_release=self.medium_delay)
        self.enter_number(lat_str)

        self.cap("6")

        if latlong.lon.degree > 0:
            self.cap("NE", delay_release=self.medium_delay)
        else:
            self.cap("SW", delay_release=self.medium_delay)
        self.enter_number(lon_str)

        if elev:
            self.cap("3")
            #
            # TODO: Check negative elevation support, for now clamp.
            #
            if elev < 0:
                elev = 0
            self.enter_number(elev)

    def enter_waypoints(self, wps, command_q=None, progress_q=None):
        cap_wp_type_buttons = dict(
            FP=4,
            IP=5,
            HB=6,
            DP=7,
            HA=8,
            ST=9
        )
        self.cap("TAC")
        for wp in wps:
            self.bkgnd_advance(command_q, progress_q)

            if wp.wp_type == "WP":
                self.cap(f"BTN_{wp.number}")
            else:
                self.cap(f"BTN_{cap_wp_type_buttons[wp.wp_type]}")

            self.enter_coords(wp.position, wp.elevation)
            self.cap("CLEAR")

    def enter_all(self, profile, command_q=None, progress_q=None):
        waypoints = self.validate_waypoints(profile.all_waypoints_as_list)

        self.bkgnd_prog_step = (1.0 / (len(waypoints) + 1)) * 100.0
        self.bkgnd_prog_cur = 0

        try:
            self.enter_waypoints(waypoints, command_q=command_q, progress_q=progress_q)
            self.bkgnd_advance(command_q, progress_q, is_done=True)
        except Exception as e:
            self.logger.debug(f"Exception raised: {e}")

'''
***********************************************************************************************************************

A-10D Driver Class

***********************************************************************************************************************
'''

class WarthogDriver(Driver):
    def __init__(self, logger, config):
        super().__init__(logger, config)
        self.limits = dict(WP=99)

    def cdu(self, num, delay_after=None, delay_release=None):
        if num == " ":
            num = "SPC"
        key = f"CDU_{num}"
        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)

    def clear_input(self, repeat=3):
        for i in range(0, repeat):
            self.cdu("CLR")

    def enter_waypoint_name(self, wp):
        result = re.sub(r'^[^A-Z]+', '', wp.name.upper())
        result = re.sub(r'[^A-Z0-9]', '', result)
        if result == "":
            result = f"WP{wp.number}"
        if len(result) > 12:
            result = result[0:11]
        self.logger.debug("Waypoint name: " + result)
        self.clear_input()
        for character in result:
            self.logger.debug("Entering value: " + character)
            self.cdu(character.upper(), delay_after=self.short_delay)

        self.cdu("LSK_3R")

    def enter_number(self, number):
        for num in str(number):
            if num in "0123456789":
                self.logger.debug(f"Entering value: " + str(num))
                self.cdu(num)

    def enter_coords(self, latlong):
        lat_str, lon_str = latlon_tostring(latlong, decimal_minutes_mode=True, easting_zfill=3, precision=3)
        self.logger.info(f"Entering coords string: {lat_str}, {lon_str}")

        self.clear_input(repeat=2)

        if latlong.lat.degree > 0:
            self.cdu("N")
        else:
            self.cdu("S")
        self.enter_number(lat_str)
        self.cdu("LSK_7L")
        self.clear_input(repeat=2)

        if latlong.lon.degree > 0:
            self.cdu("E")
        else:
            self.cdu("W")
        self.enter_number(lon_str)
        self.cdu("LSK_9L")
        self.clear_input(repeat=2)

    def enter_elevation(self, elev):
        self.clear_input(repeat=2)
        #
        # TODO: Check negative elevation support, for now clamp.
        #
        if elev < 0:
            elev = 0
        self.enter_number(elev)
        self.cdu("LSK_5L")
        self.clear_input(repeat=2)

    def enter_waypoints(self, wps, command_q=None, progress_q=None):
        self.cdu("WP", self.short_delay)
        self.cdu("LSK_3L", self.medium_delay)
        self.logger.debug("Number of waypoints: " + str(len(wps)))
        ret_wp = -1
        cur_wp = 1
        for wp in wps:
            self.bkgnd_advance(command_q, progress_q)

            self.logger.debug(f"Entering WP: {wp}")
            self.cdu("LSK_7R", self.short_delay)
            self.enter_waypoint_name(wp)
            self.enter_coords(wp.position)

            # if the elevation is exactly 0ft we don't enter it an the CDU will automatically set it to 0ft AGL
            if wp.elevation != 0:
                self.enter_elevation(wp.elevation)
            else:
                self.logger.debug("Not entering elevation because it is 0")

            if wp.is_set_cur:
                ret_wp = cur_wp
            cur_wp += 1

        if ret_wp != -1:
            self.clear_input(repeat=3)
            self.enter_number(ret_wp)
            self.cdu("LSK_3L")

    def enter_all(self, profile, command_q=None, progress_q=None):
        waypoints = self.validate_waypoints(profile.all_waypoints_as_list)

        self.bkgnd_prog_step = (1.0 / (len(waypoints) + 1)) * 100.0
        self.bkgnd_prog_cur = 0

        try:
            self.enter_waypoints(waypoints, command_q=command_q, progress_q=progress_q)
            self.bkgnd_advance(command_q, progress_q, is_done=True)
        except Exception as e:
            self.logger.debug(f"Exception raised: {e}")

'''
***********************************************************************************************************************

F-16C Driver Class

***********************************************************************************************************************
'''

class ViperDriver(Driver):
    def __init__(self, logger, config):
        super().__init__(logger, config)
        self.limits = dict(WP=127)

    def push_btn(self, key, delay_after=None, delay_release=None):
        if delay_release is None:
            delay_release = self.short_delay
        self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release)
        if delay_after is not None:
            sleep(delay_after)

    def ehsi_btn(self, btn, delay_after=None, delay_release=None):
        self.push_btn(f"EHSI_{btn}", delay_after=delay_after, delay_release=delay_release)

    def mfd_btn(self, lr, num, delay_after=None, delay_release=None):
        self.push_btn(f"MFD_{lr}_{num}", delay_after=delay_after, delay_release=delay_release)

    def icp_btn(self, num, delay_after=None, delay_release=None):
        key = f"ICP_BTN_{num}"
        if num == "ENTR":
            key = "ICP_ENTR_BTN"
        elif num == "AA_MODE":
            key = "ICP_AA_MODE_BTN"
        elif num == "AG_MODE":
            key = "ICP_AG_MODE_BTN"
        elif num == "LIST":
            key = "ICP_LIST_BTN"
        elif num == "RCL":
            key = "ICP_RCL_BTN"
        self.push_btn(key, delay_after=delay_after, delay_release=delay_release)

    def icp_ded(self, num, delay_after=None, delay_release=None):
        if delay_release is None:
            delay_release = self.short_delay

        if num == "DN":
            self.s.sendto(f"ICP_DED_SW 0\n".replace("OSB", "OS").encode(
                "utf-8"), (self.host, self.port))
        elif num == "UP":
            self.s.sendto(f"ICP_DED_SW 2\n".replace("OSB", "OS").encode(
                "utf-8"), (self.host, self.port))

        sleep(delay_release)
        self.s.sendto(f"ICP_DED_SW 1\n".replace("OSB", "OS").encode(
            "utf-8"), (self.host, self.port))

    def icp_data(self, num, delay_after=None, delay_release=None):
        if delay_release is None:
            delay_release = self.short_delay

        if num == "DN":
            self.s.sendto(f"ICP_DATA_UP_DN_SW 0\n".replace("OSB", "OS").encode(
                "utf-8"), (self.host, self.port))
        elif num == "UP":
            self.s.sendto(f"ICP_DATA_UP_DN_SW 2\n".replace("OSB", "OS").encode(
                "utf-8"), (self.host, self.port))
        elif num == "RTN":
            self.s.sendto(f"ICP_DATA_RTN_SEQ_SW 0\n".replace("OSB", "OS").encode(
                "utf-8"), (self.host, self.port))
        elif num == "SEQ":
            self.s.sendto(f"ICP_DATA_RTN_SEQ_SW 2\n".replace("OSB", "OS").encode(
                "utf-8"), (self.host, self.port))

        sleep(delay_release)
        self.s.sendto(f"ICP_DATA_UP_DN_SW 1\n".replace("OSB", "OS").encode(
            "utf-8"), (self.host, self.port))
        self.s.sendto(f"ICP_DATA_RTN_SEQ_SW 1\n".replace("OSB", "OS").encode(
            "utf-8"), (self.host, self.port))

        if delay_after is not None:
            sleep(delay_after)

    def enter_number(self, number):
        for num in str(number):
            if num in "0123456789":
                self.icp_btn(num)

    def enter_elevation(self, elev):
        #
        # Clamp negative elevations.
        # Viper avionics will not allow elevations < -1500'.
        #
        if elev < 0:
            elev = -max(elev, -1500)
            self.icp_btn("0")
        self.enter_number(elev)
        self.icp_btn("ENTR")

    def enter_coords(self, latlong):
        lat_str, lon_str = latlon_tostring(latlong, decimal_minutes_mode=True, easting_zfill=3, zfill_minutes=2, one_digit_seconds=False, precision=3)
        self.logger.info(f"Entering coords string: {lat_str}, {lon_str}")

        if latlong.lat.degree > 0:
            self.icp_btn("2")
        else:
            self.icp_btn("8")
        self.enter_number(lat_str)
        self.icp_btn("ENTR")
        self.icp_data("DN")

        if latlong.lon.degree > 0:
            self.icp_btn("6")
        else:
            self.icp_btn("4")

        self.enter_number(lon_str)
        self.icp_btn("ENTR")
        self.icp_data("DN")

    def enter_mfd_format(self, lr, osb, format, format_dflt):
        #
        # NOTE: For this to work correctly, the format mapped to the OSB should *NOT* be selected
        # NOTE: in the MFD upon entry.
        #
        self.mfd_btn(lr, osb)                           # Select OSB to set format for
        if format != format_dflt:
            self.mfd_btn(lr, osb, delay_after=0.1)      # Enter format select mode
            self.mfd_btn(lr, format, delay_after=0.1)   # Select format

    def enter_waypoints(self, wps, command_q=None, progress_q=None):
        if len(wps) > 0:
            self.icp_data("RTN")

            self.icp_btn("4", delay_after=0.1)          # Select STPT

            is_cur_seen = False
            num_backups = 1
            for wp in wps:
                self.icp_data("DN")                     # To MAN/AUTO
                self.icp_data("DN")                     # To LAT

                self.bkgnd_advance(command_q, progress_q)

                self.enter_coords(wp.position)
                if wp.elevation != 0:
                    self.enter_elevation(wp.elevation)
                if is_cur_seen:
                    num_backups += 1
                elif wp.is_set_cur:
                    is_cur_seen = True

                self.icp_data("UP")                     # To LON
                self.icp_data("UP")                     # To LAT
                self.icp_data("UP")                     # To MAN/AUTO
                self.icp_data("UP")                     # To STPT number
                self.icp_ded("UP")                      # Increment STPT number

            # "backup" the current steerpoint to select the steerpoint marked is_cur_seen.
            # if there is no such marked steerpoint, select the last one entered.
            #
            for _ in range(0, num_backups):
                self.icp_ded("DN")                      # Decrement STPT number
            self.icp_data("RTN")

    def enter_tacan(self, spec, command_q=None, progress_q=None):
        if spec is not None:
            self.bkgnd_advance(command_q, progress_q)

            self.icp_data("RTN")

            self.logger.info(f"Entering TACAN: {spec} A/A mode; EHSI TACAN")

            fields = [ str(field) for field in spec.split(",") ]

            self.icp_btn("1", delay_after=0.25)         # T-ILS
            if fields[1] == "Y":
                self.icp_btn("0")                       # Select Y
                self.icp_btn("ENTR")
            self.icp_data("DN")                         # To CHAN field
            chan = int(fields[0])
            if fields[2] == "W":
                chan = chan + 63
            self.enter_number(str(chan))                # CHAN field
            self.icp_btn("ENTR", delay_after=0.1)
            self.icp_data("SEQ", delay_after=0.1)       # REC -> T/R
            self.icp_data("SEQ", delay_after=0.1)       # T/R -> A/A TR
            
            self.icp_data("RTN", delay_after=0.1)

            self.ehsi_btn("MODE")                       # EHSI -> TACAN
            self.ehsi_btn("MODE")

            self.icp_data("RTN")

    def enter_mfd(self, mode, spec, spec_dflt, command_q=None, progress_q=None):
        if spec is not None:
            self.bkgnd_advance(command_q, progress_q)

            self.logger.info(f"Entering MFD: {mode}, spec [ {spec} ]")

            if mode == "DGFT_D":
                self.keyboard_key_with_delay(self.prefs.hotkey_dgft_cycle)
            elif mode == "DGFT_M":
                self.keyboard_key_with_delay(self.prefs.hotkey_dgft_cycle)
                self.keyboard_key_with_delay(self.prefs.hotkey_dgft_cycle)
            elif mode != "NAV":
                self.icp_btn(mode)

            # The current default setup of the Viper has a mixture of OSB 13 and 14 formats
            # selected in the four master modes (NAV, AA, AG, DGFT). For enter_mfd_format to
            # work correctly, the OSB being set up should not be selected. Start the setup
            # from OSB 12 on each MFD as in 2.8.0 none of the modes start with an OSB 12
            # format selected on either MFD.
            #
            # After setting up the formats, OSB 14 will be selected on both MFDs.
            #
            # TODO: Would work better if we could detect what is selected. Then, we could
            # TODO: act appropriately in enter_mfd_format.
            #
            fmt_osb_list = [ str(osb) for osb in spec.split(",") ]
            fmt_osb_list_dflt = [ str(osb) for osb in spec_dflt.split(",") ]

            self.enter_mfd_format("R", "12", fmt_osb_list[5], fmt_osb_list_dflt[5])
            self.enter_mfd_format("R", "13", fmt_osb_list[4], fmt_osb_list_dflt[4])
            self.enter_mfd_format("R", "14", fmt_osb_list[3], fmt_osb_list_dflt[3])

            self.enter_mfd_format("L", "12", fmt_osb_list[2], fmt_osb_list_dflt[2])
            self.enter_mfd_format("L", "13", fmt_osb_list[1], fmt_osb_list_dflt[1])
            self.enter_mfd_format("L", "14", fmt_osb_list[0], fmt_osb_list_dflt[0])

            if mode == "DGFT_D":
                self.keyboard_key_with_delay(self.prefs.hotkey_dgft_cycle)
                self.keyboard_key_with_delay(self.prefs.hotkey_dgft_cycle)
            elif mode == "DGFT_M":
                self.keyboard_key_with_delay(self.prefs.hotkey_dgft_cycle)
            elif mode != "NAV":
                self.icp_btn(mode)

            # Set up should return us to NAV master mode. In that mode, select FCR and
            # HSD formats, assuming they are defined and are not on OSB 14.
            #
            if mode == "NAV":
                osb_index = ["14", "13", "12", "14", "13", "12"]
                for i in range(len(fmt_osb_list)):
                    if (osb_index[i] != "14") and ((fmt_osb_list[i] == "20") or (fmt_osb_list[i] == "7")):
                        if i > 3:
                            self.mfd_btn("R", osb_index[i])
                        else:
                            self.mfd_btn("L", osb_index[i])

    def enter_cmds_prog(self, type, prog, command_q=None, progress_q=None):
        if prog is not None:
            self.bkgnd_advance(command_q, progress_q)

            self.logger.info(f"Entering CMDS {type} program: {prog}")
            fields = prog.split(",")

            self.enter_number(fields[0])                # BQ field
            self.icp_btn("ENTR", delay_after=0.15)
            self.icp_data('DN', delay_after=0.15)       # BQ --> BI
            self.enter_number(fields[1])                # BI field
            self.icp_btn("ENTR", delay_after=0.15)
            self.icp_data('DN', delay_after=0.15)       # BI --> SQ
            self.enter_number(fields[2])                # SQ field
            self.icp_btn("ENTR", delay_after=0.15)
            self.icp_data('DN', delay_after=0.15)       # SQ --> SI
            self.enter_number(fields[3])                # SI field
            self.icp_btn("ENTR", delay_after=0.15)
            self.icp_data('DN', delay_after=0.15)       # SI --> BQ

        else:
            self.logger.info(f"Skipping unchanged CMDS {type} program")
            sleep(0.35)

        self.icp_ded("UP", delay_after=0.25)            # Increment program number

    def enter_cmds(self, progs, command_q=None, progress_q=None):
        if progs is not None:
            self.icp_btn('LIST')                        # Select CMDS DED page
            self.icp_btn('7')
            self.icp_data('SEQ', delay_after=0.35)      # BINGO --> CHAFF

            types = [ "Chaff", "Flare" ]
            for type in types:
                for prog in progs:
                    if prog is not None:
                        prog = prog.split(";")[types.index(type)]
                    self.enter_cmds_prog(type, prog, command_q=command_q, progress_q=progress_q)

                self.icp_data('SEQ', delay_after=0.35)  # CHAFF --> FLARE

            self.icp_data("RTN")

    def enter_bulls(self, bulls, command_q=None, progress_q=None):
        if bulls is not None:
            self.icp_btn('LIST')                        # Select BULLS DED page
            self.icp_btn('0')
            self.icp_btn('8')

            if bulls == "1":
                self.icp_btn('0')                       # Set OWNSHIP mode
            self.bkgnd_advance(command_q, progress_q)

            self.icp_data("RTN")

    def enter_jhmcs(self, jhmcs, command_q=None, progress_q=None):
        if jhmcs is not None:
            self.icp_btn('LIST')                        # Select HMCS DED page
            self.icp_btn('0')
            self.icp_btn('RCL')

            fields = [ int(field) for field in jhmcs.split(",") ]
            if bool(fields[0]) == False:
                self.icp_btn('0', delay_after=0.15)     # Disable HUD BLNK, advance
            else:
                self.icp_data('DN', delay_after=0.15)   # HUD BLNK --> CKPT BLNK
            if bool(fields[1]) == False:
                self.icp_btn('0', delay_after=0.15)     # Disable CKPT BLNK, advance
            else:
                self.icp_data('DN', delay_after=0.15)   # CKPT BLNK --> DECLUTTER
            if fields[3] > 1:
                self.icp_btn('1', delay_after=0.15)     # Advance DECLUTTER
            if fields[3] > 0:
                self.icp_btn('1', delay_after=0.15)     # Advance DECLUTTER
            self.icp_data('DN', delay_after=0.15)       # CKPT BLNK --> DECLUTTER
            if bool(fields[2]) == False:
                self.icp_btn('0', delay_after=0.15)     # Disable RWR, advance

            self.bkgnd_advance(command_q, progress_q)

            self.icp_data("RTN")

    def enter_all(self, profile, command_q=None, progress_q=None):
        waypoints = self.validate_waypoints(profile.all_waypoints_as_list)

        avs_dict = profile.av_setup_dict
        avs_dict_len = len(avs_dict)
        if avs_dict is not None and avs_dict.get('f16_mfd_setup_dog') is not None:
            avs_dict_len += 1
        if avs_dict is not None and avs_dict.get('f16_bulls_setup') is not None:
            bulls_setup = avs_dict.get('f16_bulls_setup')
            avs_dict_len += 1
        else:
            bulls_setup = None
        if avs_dict is not None and avs_dict.get('f16_jhmcs_setup') is not None:
            jhmcs_setup = avs_dict.get('f16_jhmcs_setup')
            avs_dict_len += 1
        else:
            jhmcs_setup = None

        self.bkgnd_prog_step = (1.0 / (len(waypoints) + avs_dict_len + 1)) * 100.0
        self.bkgnd_prog_cur = 0

        cmds_progs = [ avs_dict.get('f16_cmds_setup_p1'),
                       avs_dict.get('f16_cmds_setup_p2'),
                       avs_dict.get('f16_cmds_setup_p3'),
                       avs_dict.get('f16_cmds_setup_p4'),
                       avs_dict.get('f16_cmds_setup_p5'),
                       avs_dict.get('f16_cmds_setup_p6')
        ]
        if cmds_progs.count(None) == 6:
            cmds_progs = None

        if avs_dict.get('f16_mfd_setup_opt'):
            mfd_nav_dflt = avs_dict.get('f16_mfd_setup_nav_dflt')
            mfd_a2a_dflt = avs_dict.get('f16_mfd_setup_air_dflt')
            mfd_a2g_dflt = avs_dict.get('f16_mfd_setup_gnd_dflt')
            mfd_dog_dflt = avs_dict.get('f16_mfd_setup_dog_dflt')
        else:
            mfd_nav_dflt = "0,0,0,0,0,0"
            mfd_a2a_dflt = "0,0,0,0,0,0"
            mfd_a2g_dflt = "0,0,0,0,0,0"
            mfd_dog_dflt = "0,0,0,0,0,0"

        try:
            self.enter_waypoints(waypoints, command_q=command_q, progress_q=progress_q)
            self.enter_tacan(avs_dict.get('tacan_yard'), command_q=command_q, progress_q=progress_q)
            self.enter_mfd("NAV", avs_dict.get('f16_mfd_setup_nav'), mfd_nav_dflt,
                           command_q=command_q, progress_q=progress_q)
            self.enter_mfd("AA_MODE", avs_dict.get('f16_mfd_setup_air'), mfd_a2a_dflt,
                           command_q=command_q, progress_q=progress_q)
            self.enter_mfd("AG_MODE", avs_dict.get('f16_mfd_setup_gnd'), mfd_a2g_dflt,
                           command_q=command_q, progress_q=progress_q)
            self.enter_mfd("DGFT_D", avs_dict.get('f16_mfd_setup_dog'), mfd_dog_dflt,
                           command_q=command_q, progress_q=progress_q)
            self.enter_mfd("DGFT_M", avs_dict.get('f16_mfd_setup_air'), mfd_dog_dflt,
                           command_q=command_q, progress_q=progress_q)
            self.enter_cmds(cmds_progs, command_q=command_q, progress_q=progress_q)
            self.enter_bulls(bulls_setup, command_q=command_q, progress_q=progress_q)
            self.enter_jhmcs(jhmcs_setup, command_q=command_q, progress_q=progress_q)
            self.bkgnd_advance(command_q, progress_q, is_done=True)
        except Exception as e:
            self.logger.debug(f"Exception raised: {e}")
