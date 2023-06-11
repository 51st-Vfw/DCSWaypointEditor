# Preferences

DCC Waypoint Editor (DCSWE) tracks a number of preferences that control how it operates.
Preferences are stored in the DCSWE application data area in the file,

```
{HOME}\Documents\DCSWE\settings.ini
```

Here, `{HOME}` is your home directory (e.g., `C:\Users\raven`). If you did not allow
DCSWE to use your `Documents` directory, application data may be saved in the main
DCSWE directory that includes the executable.

The first time you run DCSWE, it will display the preferences UI that allow you to
setup the preferences. You can access the preferences UI at any time by selecting
`DCS WE > Preferences...` from the DCSWE main menu.

The preferences UI is divided up into several sections that group together similar
settings.

## Paths & Files Section

There are three preferences in this category,

- *DCS Saved Games Directory:* Locates the directory where DCS keeps its "saved game"
  hierarchy for the DCS installation you want DCSWE to work with.
- *Tesseract Executable:* Locates the `tesseract.exe` executable installed as part of
  the tesseract installation. If this is invalid, DCSWE will not be able to capture
  coordinates from the DCS F10 map.
- *Mission File:* Locates a `.xml` or `.json` file with mission details to load through
  the `Mission > Load Mission into Jet` from the DCSWE main menu. See **TODO** for more
  information.

The `Browse` buttons to the right of each prefernce will call up a file system browser
that lets you select the specific file or directory to use for the preference.

## DSC/DCSWE Interaction Hot Keys Section

There are five preferences in this category,

- *DCS F10 Map Capture:* Captures the coordinates of the point under the mouse in the
  DCS F10 map to the coordinates pane in the UI. See **TODO* for more information.
- *Toggle Capture Mode:* Toggles the capture mode for DCS F10 map captures between
  "Add" and "Capture" modes. See **TODO** for more information.
- *Load Current Profile into Jet:* Loads the current profile from the UI into the jet.
  See **TODO** for more information.
- *Load Mission File into Jet:* Loads the mission file (specified through the *Mission
  File* preference described above) into the jet. See **TODO** for more information.
- *Quit after hot key load finishes:* Causes DCSWE to automatically quit after successfully
  loading a profile or mission file into the jet triggered by a hot key.
- *F-16 HOTAS DOGFIGHT Cycle Keybind:* Specifies the keybind for the `Cycle` command on the
  HOTAS DGFT switch. This is used by the avionics setup functionality. See **TODO**
  for more information.

## DCS BIOS Parameters Section

There are three preferences in this category,

- *Button Press (Short):* Sets the duration (in seconds) of short button presses via
  DCS-BIOS.
- *Button Press (Medium):* Sets the duration (in seconds) of medium button presses via
  DCS-BIOS.
- *Disable Export Stream Parser:* Disables the parsing of the DCS-BIOS stream that
  encodes cockpit state. This disables the use of cockpit buttons as hotkeys in
  airframes that support this.

You can control the rate of data entry into the jet by increasing or decreasing the
button press durations.

> **NOTE:** If the button press durations are too short, data entry may become
> unreliable.

The area at the bottom of the section proviees the current version of DCS-BIOS that is
installed as well as a button that will cause DCSWE to update its installation if it is
out of date.

## Miscellaneous Section

There are four preferences in this category,

- *Default Airframe:* Selects the default airframe to use in new profiles.
- *Default Avionics Setup:* Selects the default avionics setup to use in airframes that
  support this functionality (currently, the Viper). See **TODO** for more information.
- *DCS F10 clamps elevation:* When selected, DCSWE will clamp the elevation of
  coordinates it captures from the DCS F10 map to greater-than or equal-to 0. See
  **TODO** for more information.
- *DCS F10 logs OCR Output:* When selected, DCSWE will log the raw image output from
  Tesseract when capturing coordinates from the DCS F10 map. This is primarily useful
  for debugging. See **TODO** for more information.
- *Check for Updates:* When selected, DCSWE will check for updates both to DCSWE and
  DCS-BIOS when it is launched. If new versions are available, DCSWE will ask you if you
  want to update.
