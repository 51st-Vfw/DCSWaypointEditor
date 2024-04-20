# DCS Waypoint Editor

> DCS Waypoint Editor is no longer being actively supported or developed as we are moving our
> time and effort to 
> [JAFDTC](https://github.com/51st-Vfw/JAFDTC).
> We encourage you to consider transitioning to that DTC.
>
> It's been a good run, hopefully you found it useful.

DCS Waypoint Editor (DCSWE) is an application that allows you to input waypoints
(including airframe-specific waypoints such as the MSN preplanned missions waypoints in
the F/A-18C Hornet) and other data, such as avionics configurations, into DCS aircraft.
Currently DCSWE supports the following airframes,

* A-10C Warthog
* AV-8B Harrier
* F-14A/B Tomcat
* F-16C Viper
* F/A-18C Hornet
* M-2000C Mirage

Not all features are supported on all airframes. This document provides a quick overview
of DCSWE. See the
[documentation](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/README.md)
in the repository for detailed documentation.

This 51st VFW DCSWaypointEditor is a fork of Santi871's
[DCSWaypointEditor](https://github.com/Santi871/DCSWaypointEditor)
application and based on Santi871's work.

## Building & Installing

See the
[build documentation](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/build.md)
for details on how to build DCSWE from its Python source code.

To install DCS Waypoint Editor,

1. Download and install [Google Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Download and install [DCS-BIOS](https://github.com/DCSFlightpanels/dcs-bios)
3. Unzip the contents of the `dcs_wp_editor.zip` from the
   [DCSWE releases](https://github.com/51st-Vfw/DCSWaypointEditor/releases) to a folder
   (or use a version you have built locally)
4. Run `dcs_wp_editor.exe` and perform the first time setup

> **NOTE**: DCSWE is *not* compatible with the HUB version of DCS-BIOS, you must use the
> DCSFlightpanels version linked above.

When you first run DCSWE, it will ask you to setup a directory for application data in
your `Documents` directory. If you do not want to create this directory, DCSWE will fall
back to saving application data in the installation directory.

## Where to Go Next

This reaminder of this README provides a brief overview of some basic features of DCSWE.
This is not an exhaustive look, but instead it focuses on basic operations. More involved
capabilities, such as Mission Packs, are not covered here. For further details on the
complete operation of DCSWE, see the material in the
[documentation](https://github.com/51st-Vfw/DCSWaypointEditor/tree/master/documentation)
directory of the repository.

## Profiles Overview

DCSWE creates "profiles" that contain mission information such as waypoints and avionics
configurations. Waypoints and similar items (e.g., F/A-18 JDAM preplanned missions) can
be added to a profile through a variety of approaches,

- Manually entering coordinates
- Capturing coordinates from the DCS F10 map via optical text recognition
- Entering coordinates from pre-defined points of interest
- Importing coordinates from a CombatFlite mission XML export
- Importing coordiantes from a DCSWE JSON file

These profiles are stored in a database local to the DCSWE installation. You can save,
copy, delete, or revert profiles using the commands on the "Profiles" menu. The drop-down
list at the top of the profiles panel lists the currently defined profiles from which you
can select.

DCSWE can import and export from and to profiles in a variety of formats. The import and
export commands can be found in the "Import" and "Export" items on the "Profiles" menu.
The formats include JSON, encoded JSON, and CombatFlite mission XML export. Depending
on the operation, the target can be a file or the clipboard.

You may add more preset locations by adding more JSON formatted files in the `data` folder.
Such files should follow the format in the `pg.json` and `cauc.json` files that come with
the distribution.

### Entering Coordinates Manually

To manually enter a waypoint,

1. Choose a waypoint type (e.g., WP for a regular waypoint, MSN for a JDAM preplanned mission)

2. Enter the latitude and longitude (decimal seconds are supported)

3. Enter the elevation in feet (optional for regular waypoints, mandatory for JDAM
   preplanned missions)

4. (Optional) Choose a sequence to assign the waypoint to

5. (Optional) Assign a name to the waypoint

6. Click `Add` to add the waypoint to the list of waypoints in the active profile

### Entering Coordinates from the DCS F10 Map

To capture the coordinates for a waypoint from the DCS F10 map,

1. Enable coordinate capture in DCSWE by clicking the "Enable capture from DCS F10 map..."
   checkbox

2. Select the desired destination of the coordinates from the pop-up menu:
    1. "Coordinate Panel" to place the captured coordinates in the coordinate panel of the UI.
    2. "New Waypoint" places the captured coordinates in a newly-created waypoint in the
       current profile.

3. Make sure your F10 map is in [DD MM SS.ss](https://i.imgur.com/9GIU7pJ.png) or
   [MGRS](https://i.imgur.com/T7lBvlx.png) coordinate format.
   You cycle coordinate formats with `<LALT>+Y` in the DCS F10 map.

4. In the DCS F10 map, hover your mouse over your desired position

5. Press the key you bound to DCS F10 map capture in the preferences (default is `<CTRL>+T`),
   DCSWE will beep and save the coordinates based on the destination set earlier

If you are capturing to the coordiante panel, you must explicitly add the waypoint to the
current profile using the "Add" button. Subsequent captures will over-write the coordinates
in the panel.

You can toggle between the capture destinations with the key you bound to toggle capture mode
in the preferences (default is `<CTRL>+<SHIFT>+T`). DCSWE will provide audio feedback on the
toggle and capture actions so you do necessarily need to switch back to the DCSWE UI.

The key bindings may be changed through the preferences and should not conflict with any DCS
key bindings.

DCSWE does not currently support capture from the DCS F10 map in VR.

### Point-of-Interest Coordinates

You may select a position from a list of preset coordinates. Coordinates for all Caucasus and
PG airfields and BlueFlag FARPS are included. Typing in the pop-up menu and then clicking on
the "Filter" button allows you to filter the list of points of interest.

### Hornet JDAM Pre-Planned Missions

Hornet JDAM preplanned missions work in a similar way to waypoints, however, you **must**
select the correct station for the mission to be assigned using the station selector.

### Loading Data into Your Aircraft

DCSWE can directly drive the clickable cockpits in a DCS jet to enter data into a jet.
When entering data, DCSWE uses the airframe selected by the "Airframe" pop-up menu in the
profiles panel to determine which cockpit it will need to operate (if the pop-up does not
match the jet in DCS, data will not be entered correctly). DCSWE can enter data from one of
two sources:

- The current profile selected and displayed in the DCSWE UI.
- A mission file at a known location (set through preferences) in a format DCSWE supports
  (JSON or an XML export of a CombatFlite mission)

Entering data can be triggered from either the DCSWE UI directly or from a hotkey in DCS. By
default, the current profile is loaded with `<CTRL>+<ALT>+T` and the mission file is loaded
with `<CTRL>+<ALT>+<SHIFT>+T`. The bindings may be changed through DCSWE preferences and
should not conflict with any DCS keys. With hotkeys, it is possible to setup your jet from
DCS without switching out of DCS.

The steps for entering data are similar for all airframes. Once the sequence is started, it
can be cancelled if necessary. The airframe in the profile should match the aircraft you are
trying to enter data into. Further, to avoid issues, you should aovid interacting with the
cockpit while DCSWE is entering data. The following sections provide some airframe-specific
pointers.

#### AV-8B Harrier

1. Make sure the main EHSD page is on the left AMPCD (left screen).

2. Trigger entry as described above.

#### F-16C Viper

For the Viper, the sequence will first reset the DED to the main page before using the
steerpoint DED page to enter each waypoint. There is no specific state the jet needs to
be in prior to triggering entry as described above.

#### F/A-18C Hornet

1. Make sure the main HSI page is on the AMPCD (bottom screen) if you are entering waypoints.
 
2. If you are entering JDAM preplanned missions, make sure the JDAM preplanned missions page
   is on the left DDI

![pages](https://i.imgur.com/Nxr9qKX.png)

3. Trigger entry as described above.

#### M-2000C Mirage

For the Mirage, there is no specific state the jet needs to be in prior to triggering entry
as described above.

## Known issues

* Attempting to enter sequence #2 or #3 without sequence #1 will not work.

## Other Credits

- [DCSWaypointEditor](https://github.com/Santi871/DCSWaypointEditor) Baseline source code
- [DCS-BIOS](https://github.com/DCSFlightpanels/dcs-bios) is redistributed under the GPLv3 license
- [PyMGRS](https://github.com/aydink/pymgrs) by aydink
