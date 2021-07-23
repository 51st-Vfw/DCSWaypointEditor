# Avionics Setup

DCC Waypoint Editor (DCSWE) currently supports avionics setup for the F-16C Viper. The
following state in the Viper's avionics can be setup (in addition to waypoints):

- TACAN in yardstick mode
- Selected MFD formats for use in NAV, AA, AG, and DGFT master modes

At present, this support is specific to the Viper, though other airframes may have
analogous state.

> **NOTE:** This functionality will eventually be replaced by DCS DTC support if and
> when that happens.

As DCSWE cannot always determine avionics state (e.g., it is difficult to determine
which MFD format is currently selected), DCSWE makes some assumptions around the initial
configuration of the avionics.

> **NOTE:** If the state does not match the expected initial configuration, the updates
> that DCSWE performs may not yield the desired results.

Avionics setup can be done as part of loading a profile or a mission (in DCSWE JSON
format) into the jet. It is not possible at present to set up the avionics through
non-native mission setups (e.g., CombatFlite). To setup the avionics while loading
a mission from a CombatFlite import, you could import the waypoints from CombatFlite
and use a separate profile (with no waypoints) to provide the avionics.

As with waypoint entry, it is important to minimize interactions with the jet while
DCSWE is driving the cockpit switches.

## TACAN Yardstick

The TACAN yardstick allows the user to specify a TACAN channel and a role (flight lead
or wingman) and will set up the TACAN appropriately. Yardsticks are setup with the
flight lead on channel C and the wingmen on channel C+63 (note that this implies that
legal channels for yardsticks are between 1 and 63). DCSWE handles the lead/wingman
channel modification automatically.

For example, if the UI sets up for a TACAN yardstick on 38Y, the flight lead or wingman
role will determine what is actually programmed into the jet,

- For a flight lead, the TACAN is set to channel 38Y in AA T/R mode.
- For a wingman, the TACAN is set to channel 101Y in AA T/R mode.

In both cases, the EHSI will be switched to TACAN mode.

For TACAN setup to work correctly, DCSWE expects the following initial conditions:

- TACAN band should be "X"
- TACAN operation mode should be "REC"
- EHSI mode should be "NAV"

The initial state of the Viper when powered on should match these requirements.

## MFD Formats

Each MFD on the Viper can display one of three formats (e.g., FCR, TGP, HSD) that are
selected by OSB 12, 13, and 14. The formats are tied to the current master mode (NAV,
AA, AG, DGFT) allowing each master mode to have its own unique setup of MFD formats.
DCSWE provides the ability to change the MFD format configuration from the defaults.

DCSWE allows per-master-mode selection of format sets to update. That is, you can update
only DGFT while leaving the other setups in their default configuration.

For MFD format setup to work correct, DCSWE expects the following initial conditions:

- Master mode should be NAV
- For all master modes that are to be updated, the current format on the left and right
  MFDs may not be whatever format is mapped to OSB 12
- The HOTAS DOGFIGHT switch `DOGFIGHT` position in DCS must be bound to the hotkey
  specified in the DCSWE preferences
- The HOTAS DOGFIGHT switch `CENTER` position in DCS must be bound to the hotkey
  specified in the DCSWE preferences
- DCS must be in the foreground so that it can recieve key presses

The initial state of the Viper when powered on should match these requirements.

## Preferences

There are four preferences that control the behavior of the avionics setup functionality.

- *Default Avionics Setup:* Specifies the default avionics setup to use when creating new
  profiles, the setup "DCS Default" corresponds to the default setup of the jet in DCS.
  For airframes other than the Viper, this setting is effectively always "DCS Default".
- *Use When Setup Unknown:* When set, this preference causes DCSWE to use the default
  avionics setup in situations where it does not have information on the avionics setup.
  For example, if this is set, a profile created from CombatFlite would use the default
  setup. When not set, DCSWE does not change avionics setup (i.e., it behaves as if the
  default were "DCS Default")
- *F-16 HOTAS DOGFIGHT Dogfight:* Specifies the keybind for the `DOGFIGHT` position on
  the HOTAS DGFT switch, the keybind should use `shift`, `alt`, or `ctrl`.
- *F-16 HOTAS DOGFIGHT Center:* Specifies the keybind for the `CENTER` position on the
  HOTAS DGFT switch, the keybind should use `shift`, `alt`, or `ctrl`.

These can be set throught the DCSWE preferences, strangely enough. Note that the
`DOGFIGHT` and `CENTER` hotkeys will need to also be set up through the DCS control
setup in DCS.