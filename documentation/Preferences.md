# Preferences

DCC Waypoint Editor (DCSWE) tracks a number of preferences that control how it operates.
Preferences are typically stored in the DCSWE application data area in the file,

```
{HOME}\Documents\DCSWE\settings.ini
```

Here, `{HOME}` is your home directory (e.g., `C:\Users\raven`).

> If you did not allow DCSWE to use your `Documents` directory, application data may be
> saved in the main DCSWE directory that includes the executable.

The first time you run DCSWE, it will display the preferences UI that allow you to
setup the preferences. You can access the preferences UI at any time later by selecting
"`DCS WE > Preferences...`" from the DCSWE main menu.

The preferences UI is divided up into several tabs that group together similar settings.
After making changes, click the "`OK`" button at the bottom of the window or close widget
at the right edge of the window's title bar to save your changes.

## Filesystem Preferences

This tab of the preferences window specifies filesystem-related configuration.

![Preferences: Filesystem](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/images/Prefs_Filesystem.jpg)

There are three preferences shown in this tab,

- *DCS Saved Games Directory:* Locates the directory where DCS keeps its "saved game"
  hierarchy for the DCS installation you want DCSWE to work with.
- *Tesseract Executable:* Locates the `tesseract.exe` executable installed as part of
  the tesseract installation. If this is invalid, DCSWE will not be able to capture
  coordinates from the DCS F10 map.
- *Mission File:* Locates a `.xml` or `.json` file with mission details to load through
  the "`Mission > Load Mission into Jet`" from the DCSWE main menu. See [DCSWE & DCS](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/DCSWE_DCS.md)
  for more information.

To change one of these preferences, click the "`Browse`" buttons to the right of each
preference will call up a file system browser that lets you select the specific file or
directory to use for the preference.

## Keyboard Preferences

This tab of the preferences window specifies keyboard-related configuration.

![Preferences: Keyboard](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/images/Prefs_Keyboard.jpg)

There are two general classes of preferences in this tab: DCSWE-related hot keys for
use when DCS is in the foregoround and DCS aircraft control key binds.

Hot keys are made up of zero or more modifiers ("ctrl", "shift", or "alt") with a
keyboard key. Modifers may include "left" or "right" to specify a particular modifier
key. For example, "right ctrl+alt+R" specifies pressing the right `CTRL` key, any `ALT`
key, and the "`R`" key.

### DCSWE Hot Keys

You can use the DCSWE hot keys to interact with key DCSWE functionality when DCS is in
the foreground. The preferences include,

- *DCS F10 Map Capture:* Captures the coordinates of the point under the mouse in the
  DCS F10 map to the coordinates pane in the UI. See **TODO* for more information.
- *Toggle DCS F10 Capture Mode:* Toggles the capture mode for DCS F10 map captures
  between "Add" and "Capture" modes. See
  [DCSWE & DCS](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/DCSWE_DCS.md)
  for more information.
- *Load Current Profile into Jet:* Loads the current profile from the UI into the jet.
  See **TODO** for more information.
- *Load Mission File into Jet:* Loads the mission file (specified through the *Mission
  File* preference described above) into the jet. See
  [DCSWE & DCS](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/DCSWE_DCS.md)
  for more information.
- *Toggle Item Select Type:* TODO
- *Select Next Item of Type:* TODO
- *Quit after hot key load finishes:* Causes DCSWE to automatically quit after
  successfully loading a profile or mission file into the jet triggered by a hot key.

### DCS Aircraft Controls

To interact with some airframes, DCSWE may generate key presses that map to cockpit
controls in the airframe. The preferences include,

- *F-16 HOTAS / DOGFIGHT Cycle:* Specifies the keybind for the `Cycle` command on the
  HOTAS DOGFIGHT switch. This is used by the avionics setup functionality. See
  [Avionics Setup: F-16C](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Avionics_Setup_F16.md)
  for more information.

These preferences should be set up consistent with the key binds the DCS settings specify
for the associated airframe.

## DCS-BIOS Parameters

This tab of the preferences window specifies keyboard-related configuration.

![Preferences DCS-BIOS](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/images/Prefs_DCS_BIOS.jpg)

There are three preferences in this category,

- *Button Press Delay (Short):* Sets the duration (in seconds) of short button presses
  via DCS-BIOS.
- *Button Press Delay (Medium):* Sets the duration (in seconds) of medium button presses
  via DCS-BIOS.
- *Disable Parsing of Export Stream:* Disables the parsing of the DCS-BIOS stream that
  encodes cockpit state. This disables the use of cockpit buttons as hotkeys in
  airframes that support this functionality. See **TODO** for more information.

You can control the rate of data entry into the jet by increasing or decreasing the
button press durations.

> **NOTE:** If the button press durations are too short, data entry may become
> unreliable.

The area at the bottom of the section provides the current version of DCS-BIOS that is
installed as well as a button that will cause DCSWE to update its installation if it is
out of date.

## Miscellaneous

This tab of the preferences window specifies keyboard-related configuration.

![Preferences: Miscellaneous](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/images/Prefs_Misc.jpg)

There are five preferences in this category,

- *Default Airframe:* Selects the default airframe to use in new profiles.
- *Default Avionics Setup:* Selects the default avionics setup to use in airframes that
  support this functionality. See
  [Avionics Setup](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Avionics_Setup.md)
  for more information.
- *DCS F10 capture clamps elevation:* When selected, DCSWE will clamp the elevation of
  coordinates it captures from the DCS F10 map to greater-than or equal-to 0. See
  [DCSWE & DCS](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/DCSWE_DCS.md)
  for more information.
- *DCS F10 capture logs OCR Output:* When selected, DCSWE will log the raw image output
  from Tesseract when capturing coordinates from the DCS F10 map. This is primarily
  useful for debugging. See
  [DCSWE & DCS](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/DCSWE_DCS.md)
  for more information.
- *Check for Updates at Launch:* When selected, DCSWE will check for updates both to
  DCSWE and DCS-BIOS when it is launched. If new versions are available, DCSWE will ask
  you if you want to update.
