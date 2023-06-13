# DCS Waypoint Editor and DCS

DCSWE and DCS interact around three main tasks: loading DCSWE profiles into the jet,
loading DCSWE mission packages into the jet, and capturing coordinates from the DCS F10
map.

## Loading Profiles into the Jet

TODO

### Using Cockpit Buttons as Hot Keys

DCSWE supports mapping unused (or rarely used) cockpit buttons onto DCSWE hotkeys to
allow the user to interact with DCSWE without needing to use the keyboard. Currently,
this is only supported on the F-16C Viper.

The Viper uses three of the FLIR keys at the right of the ICP as DCSWE hotkeys. As the
FLIR is not supported in the block 50 version of the Viper, these buttons are non-
functional (though DCS does track interactions with the buttons).

![F-16C Viper ICP](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/images/F16_ICP.jpg)

The buttons of interest are the "`Wx`" button just to the right of the FLIR text and
the "`Up/Dn`" rocker switch just below that button. The buttons operate as follows,

- `Wx`: triggers the "`Profile > Load Profile into Jet`" function from the main DCSWE
  menu which load the current profile into the jet.
- `Dn`: toggles between advancing the selection in the profile list or avionics setup
  list in the user interface. A voice cue will tell you which item is active.
- `Up`: advances the item selected by the `Dn` button. For example, if the `Dn` button
  selects the avionics setup, pressing `Up` will cycle between the available avionics
  setups.


For this functionality to work, export parsing must be enabled in the
`DCS-BIOS` tab of the
[DCSWE Preferences](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Preferences.md).

## Loading Mission Packages into the Jet

TODO

## Capturing Coordinates from the DCS F10 Map

TODO