'''
*
*  gui_util.py: GUI utilities and support
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

import PySimpleGUI as PyGUI
import psutil
import threading
import queue

from time import sleep
from win32gui import GetWindowText, GetForegroundWindow

from src.logger import get_logger

logger = get_logger(__name__)

# maps UI text : internal type for airframe pulldown menus in the ui.
#
airframe_map = { "A-10C Warthog" : "warthog",
                 "AV-8B Harrier" : "harrier",
                 "F-14A/B Tomcat" : "tomcat",
                 "F-16C Viper" : "viper",
                 "F/A-18C Hornet" : "hornet",
                 "M-2000C Mirage" : "mirage"
}


# return list of supported airframes. second token (" " separated) of items is internal name.
#
def airframe_list():
    return list(airframe_map.keys())

# convert ui airframe text to internal airframe type.
#  
def airframe_ui_text_to_type(ui_text):
    type = airframe_map[ui_text]
    if type is None:
        type = "viper"
    return type

# convert interanl airframe type to text suitable for ui
#
def airframe_type_to_ui_text(type):
    hits = [k for k,v in airframe_map.items() if v == type]
    if (len(hits) == 0):
        hits = ["F-16C Viper"]
    return hits[0]

# add strike-through in gui-text
#
def gui_text_strike(text):
    result = '\u0336'
    for i, c in enumerate(text):
        result = result + c
        if i != len(text)-1:
            result = result + '\u0336'
    return result

# remove strike-through in gui text
#
def gui_text_unstrike(text):
    return text.replace('\u0336', '')

# ui for exceptions.
#
def gui_exception(exc_info):
    return PyGUI.PopupOK("An exception occured and the program terminated execution:\n\n" + exc_info)

# handle an update request if the current and new version of a component are not the same.
#
# installation function should return version string on success (user is notified via ui), empty
# string on error (user is notified via ui), or None on no result (user is not notified).
#
def gui_update_request(comp, cur_vers, new_vers, install_fn, inform_update=True):
    message = f"A new version of {comp} is available ({new_vers}).\nDo you want to update from {cur_vers}?"
    if cur_vers != new_vers and PyGUI.PopupYesNo(message, title="New Version Available") == "Yes":
        logger.info(f"Update {comp} from {cur_vers} to {new_vers} accepted")
        try:
            version = install_fn()
        except Exception as e:
            version = None
        if version is not None and version != "" and inform_update:
            PyGUI.Popup(f"{comp} {new_vers} was successfully installed.", title="Success")
        elif version is None:
            PyGUI.Popup(f"{comp} {new_vers} installation failed.", title="Error")
        return True
    elif cur_vers != new_vers:
        logger.info(f"Update {comp} from {cur_vers} to {new_vers} declined")
    return False

# handle an initial setup request.
#
def gui_new_install_request(data_path):
    data_path = data_path[:-1]
    message = f"Save DCSWE data in {data_path}, creating it if necessary?\n" + \
              f"If not, DCSWE data is stored in the application directory."
    if PyGUI.PopupYesNo(message, title="New Install Detected") == "Yes":
        return True
    else:
        return False

# handle a request to update DCS-BIOS configuration file. returns True if accepted, False otherwise.
#
def gui_update_dcsbios_cfg_request(install_fn):
    message = f"To allow cockpit buttons to trigger DCSWE profile loads and better operate with DCSWE," + \
              f" the DCS-BIOS configuration file BIOSConfig.lua should be updated.\n\n" + \
              f" Update this file (current file will be backed up)?"
    if PyGUI.PopupYesNo(message, title="Update DCS-BIOS Configuration") == "Yes":
        logger.info(f"DCS-BIOS config update accepted")
        try:
            result = install_fn()
        except Exception as e:
            result = False
        if not result:
            PyGUI.Popup(f"DCS-BIOS BIOSConfig.lua was successfully updated.", title="Success")
            return True
        else:
            PyGUI.Popup(f"DCS-BIOS BIOSConfig.lua udpate failed.", title="Error")
    else:
        logger.info(f"DCS-BIOS config update declined")
    return False

# run a background operation with a modal progress ui.
#
# the backgrounded operation (bop_fn) must take two named args: progress_q and cancel_q in
# addition to any unamed arguments given by the tuple in bop_args.
#
#   progress_q (queue)  operation puts numbers on [0,100] representing the completion
#                       percentage, "DONE" when the operation has finished or is cancelled
#   command_q (queue)   gui puts "CANCEL" in this queue to indicate the operation should
#                       stop processing, clean up, and exit
#
def gui_backgrounded_operation(title, bop_fn=None, bop_args=None):

    # we will prepare the layout but *not* actually create the window. this avoids some
    # potential issues caused when window layering changes while DCSWE is running in the
    # background.
    #
    layout = [[PyGUI.Text("Progress:", size=(8,1), justification="right"),
               PyGUI.ProgressBar(100, key='ux_progress', size=(25,16)),
               PyGUI.Button("Cancel", key='ux_cancel', size=(10,1), pad=(6,16))]]
    window = None
    progress = 0

    # launch a background thread to run the backgrounded work in the background.
    #
    progress_q = queue.Queue()
    command_q = queue.Queue()
    bop_kwargs={ 'progress_q' : progress_q, 'command_q' : command_q }

    bop_thread = threading.Thread(target=bop_fn, args=bop_args, kwargs=bop_kwargs)
    bop_thread.start()

    logger.debug(f"Starting progress ui for backgrounded op, thread {bop_thread.ident}")

    # main loop. we will run this without any ui for as long as the front window is the
    # DCS window. this ensures that we don't disturb the window stack (taking dcs out of
    # focus and potentially causing it to miss keypresses) if DCSWE is running in the
    # background. once DCS is not frontmost, we'll create the window and continue.
    #
    while True:
        fgwin_title = GetWindowText(GetForegroundWindow())
        if not bop_thread.is_alive() and progress_q.empty():
            logger.debug("Backgrounded op thread has passed beyond the veil")
            break
        elif (fgwin_title != "Digital Combat Simulator" and
              fgwin_title != "DCS.openbeta" and
              fgwin_title != "DCS") and (window is None):
            window = PyGUI.Window(title, layout, modal=True, finalize=True, disable_close=True)
            window['ux_progress'].update(progress)

        if window is not None:
            event, _ = window.read(timeout=250, timeout_key='ux_timeout')
        else:
            sleep(0.25)
            event = 'ux_timeout'

        if event == 'ux_timeout':
            try:
                progress = progress_q.get(False)
                if progress == "DONE":
                    logger.debug(f"Backgrounded op progress: DONE")
                    break
                else:
                    logger.debug(f"Backgrounded op progress: {progress:.2f}")
                    if window is not None:
                        window['ux_progress'].update(progress)
            except queue.Empty:
                pass
        elif event == 'ux_cancel':
            logger.debug("Sending cancel to backgrounded op, waiting for join")
            window['ux_cancel'].update(text="Cancelling...", disabled=True)
            command_q.put("CANCEL")

    if window is not None:
        window.close()

# use psutil to figure out if DCS is running, potentially notifing user if not.
#
def gui_verify_dcs_running(message=None, is_notify=True):
    try:
        is_running = "DCS.exe" in (proc.name() for proc in psutil.process_iter())
    except:
        is_running = False
    if not is_running and is_notify:
        PyGUI.Popup(f"{message}DCS is not currently running.", title="Error")
    return is_running

# select one option from a list of options with OK/cancel.
#
def gui_select_from_list(message="Select an option", title="Select", values=[]):
    if len(values) == 0:
        return None

    layout = [[PyGUI.Text(f"{message}:", size=(40,2))],
              [PyGUI.Combo(values=values, default_value=values[0], key='ux_option_combo',
                           readonly=True, size=(42,1))],
              [PyGUI.Button("OK", key='ux_ok', size=(10,1)),
               PyGUI.Button("Cancel", key='ux_cancel', size=(8,1))]]
    window = PyGUI.Window(title, layout, modal=True, finalize=True, disable_close=True)

    selection = None
    while True:
        event, values = window.Read()
        if event == 'ux_ok':
            selection = values['ux_option_combo']
            break
        elif event == 'ux_cancel':
            break
    
    window.close()

    return selection

