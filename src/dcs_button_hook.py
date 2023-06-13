'''
*
*  dcs_button_hook.py: Hooks DCS clickable cockpit button presses
*
*  Copyright (C) 2023 twillis/ilominar
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

import socket

from src.gui_util import gui_is_dcs_foreground
from src.logger import get_logger

from time import sleep

# maps internal airframe name onto map defining a set of cockpit buttons to use for loading
# a profile ("load"), toggling the item select type ("type"), and selecting the next item
# ("isel"). each value is a  { <address>, <mask>, <shift>, <value> } tuple that defines the
# export state values to look for. the tuple is a map with keys "a", "m", "s", and "v" for
# <address>, <mask>, <shift>, and <value> respectively.
#
# see the .json airframe files in Scripts/DCS-BIOS/doc/json from the DCS-BIOS repository for
# details on the appropriate <address>, <mask>, and <shift> values for a particular button.
#
exp_button_map = {
    "viper" : { "load" : { "a" : 17450, "m" :   64, "s" :  6, "v" : 1 },    # ICP/FLIR Wx
                "type" : { "a" : 17450, "m" : 6144, "s" : 11, "v" : 0 },    # ICP/FLIR INCR dn
                "isel" : { "a" : 17450, "m" : 6144, "s" : 11, "v" : 2 },    # ICP/FLIR INCR up
    }
}

17450, 65, 6, 1
17450, 6144, 11, 0/2

logger = get_logger(__name__)


def dcs_exp_parse_thread(wpe_gui, host = "127.0.0.1", port = 7777):

    logger.info("DCS-BIOS export stream parser thread starting")

    # create a udp socket for the export stream. default is localhost:7777.
    #
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(2)
    sock.bind((host, port))

    af_btn_map = None

    # TODO: do we want to throttle this a bit?
    while not wpe_gui.is_dcswe_exiting:

        # if dcs is not in the foreground, we will track the current airframe to update the
        # export details we are going to track. we'll skip checking the export stream at this
        # point since dcs is not foreground.
        #
        if not gui_is_dcs_foreground():
            exp_params = exp_button_map[wpe_gui.profile_airframe()]
            if exp_params is not None:
                af_btn_map = {
                    wpe_gui.hkey_profile_enter_in_jet : exp_params["load"],
                    wpe_gui.hkey_item_sel_type_toggle : exp_params["type"],
                    wpe_gui.hkey_item_sel_advance             : exp_params["isel"],
                }
            else:
                af_btn_map = None
            sleep(4)
            continue
        elif af_btn_map == None:
            sleep(4)
            continue

        # try to pull data from the export stream. if the receive fails, we will loop back
        # around and try again. note that the stream will not come up until player is in
        # pit and exports have started.
        #
        try:
            data, addr = sock.recvfrom(4096)
        except socket.error as e:
            continue

        # search from the start of the received bytes for a frame delimiter: { 0x55 0x55 0x55 0x55 }
        # to find the stream index from which we will start parsing. this will effectively throw away
        # all bytes from before the frame delimiter.
        #
        i = 0
        while i < len(data):
            if ((data[i] == 0x55) and (data[i+1] == 0x55) and (data[i+2] == 0x55) and (data[i+3] == 0x55)):
                i += 4
                break
            i += 1

        # scan forward from the first delimiter we found in the received byte stream and process the
        # elements. each element is encoded in the stream as { <addr> <len> <data> } where <addr> is
        # a 2-byte addres, <len> is a 2-byte data length, and <data> is <len> bytes of element data.
        # <addr>, <len>, and integer data are little-endian. if we find another frame delimiter, we
        # will skip over it and continue processing.
        #
        # if we find an element that writes to a button we track, we will trigger the appropriate load
        # hot key in the main ui.
        #
        while i < len(data):
            if ((data[i] == 0x55) and (data[i+1] == 0x55) and (data[i+2] == 0x55) and (data[i+3] == 0x55)):
                i += 4
            elif len(data) > (i + 3):
                btn_addr = (data[i+1] << 8) + data[i]
                btn_len  = (data[i+3] << 8) + data[i+2]
                if len(data) > (i + 3 + btn_len):
                    if btn_len == 2:
                        btn_data = (data[i+5] << 8) + data[i+4]
                    elif btn_len == 4:
                        btn_data = (data[i+7] << 24) + (data[i+6] << 16) + (data[i+5] << 8) + data[i+4]
                    i += 4 + btn_len

                    for hkey_fn, btn_info in af_btn_map.items():
                        if btn_addr == btn_info["a"]:
                            btn_val = (btn_data & btn_info["m"]) >> btn_info["s"]
                            if btn_val == btn_info["v"]:
                                logger.debug(f"Export press: 0x{btn_info['a']:x} & 0x{btn_info['m']:x} >> {btn_info['s']} = {btn_info['v']}")
                                hkey_fn()

                else:
                    break
            else:
                break

    logger.info("DCS-BIOS export stream parser thread exiting")