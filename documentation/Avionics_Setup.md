# Avionics Setup

DCC Waypoint Editor (DCSWE) currently supports avionics setup for the F-16C Viper. The
following state in addition to
[steerpoints](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Waypoint_Setup.md)
from the Viper's avionics can be set up:

- TACAN yardstick
- MFD formats for use on the left and right MFDs in NAV, AA, AG, and DGFT master modes
- CMDS programs for chaff and flares
- Bullseye display on FCR and HSD MFD formats
- JHMCS setup

At present, this support is specific to the Viper. As other airframes can have some
analogous state, we may extend the support in the future.

> **NOTE:** This functionality eventually will be replaced by DCS DTC support.

Because DCSWE cannot always determine avionics state (e.g., DCSWE is unable to determine
which MFD format is currently selected), DCSWE makes several assumptions, detailed below,
around the initial configuration of the avionics. These assumptions match the state of
the avionics following a cold start before any modifications are made to avionics state.

> **NOTE:** If the state does not match the expected initial configuration, the updates
> that DCSWE performs may not yield the desired results.

Avionics setup can be done as part of loading a profile or a mission (in DCSWE JSON
format) into the jet. For non-native mission setups (e.g., from a CombatFlite export),
you can either import into a native DCSWE profile and specify the avionics setup through
that DCSWE profile, or tell DCSWE (through preferences) to use a default avionics setup
when configuring the jet using non-native sources.

As with waypoint entry, it is important to minimize interactions with the jet while
DCSWE is driving the cockpit switches.

## Preferences

There are three
[preferences](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Preferences.md)
that control the behavior of the avionics setup functionality.

- *Default Avionics Setup:* Specifies the default avionics setup to use when creating new
  profiles, the setup "DCS Default" corresponds to the default setup of the jet in DCS.
  For airframes that do not support avionics setup, this setting is effectively always
  "DCS Default".
- *Use When Setup Unknown:* When set, this preference causes DCSWE to use the default
  avionics setup in situations where it does not have information on the avionics setup.
  For example, if this is set, when loading a mission from a CombatFlite export file
  will use the specified default avionics setup. When not set, DCSWE will not change
  avionics setup if it does not have information on the desired setup (i.e., it behaves
  as if the default were "DCS Default")
- *F-16 HOTAS DGFT Cycle:* Specifies the keybind for the `Cycle` command on the
  HOTAS DGFT switch in the Viper, the keybind should use at least one of `shift`, `alt`,
  or `ctrl`. The keybind should be specified keeping in mind that DCS uses specific
  modifiers (left or right `shift`, for example).

These can be set throught the
[DCSWE preferences](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Preferences.md),
strangely enough. Note that the
`DGFT Cycle` hotkey will need to also be set up through the control options in DCS
(specifically, see the HOTAS section in the "F-16C Sim" controls).

## TACAN Yardstick

The TACAN yardstick support allows the user to specify a TACAN channel and a role
(flight lead or wingman) and will set up the TACAN appropriately. Yardsticks are set
up with the flight lead on channel C and the wingmen on channel C+63 (note that this
implies that legal channels for yardsticks are between 1 and 63, though legal TACAN
channels are between 1 and 126). DCSWE handles the lead/wingman channel modification
automatically.

For example, if the user configures the DCSWE UI to set up a TACAN yardstick on 38Y,
the flight lead or wingman role selected in the UI will determine what is actually
programmed into the jet,

- For a flight lead, the TACAN is set to channel 38Y in AA T/R mode.
- For a wingman, the TACAN is set to channel 101Y in AA T/R mode.

In both cases, the EHSI will be also switched to TACAN mode so you can check DME to
see if the yardstick is sweet or sour.

For TACAN setup to work correctly, DCSWE expects the following initial conditions in
the Viper:

- TACAN band should be "X"
- TACAN operation mode should be "REC"
- EHSI mode should be "NAV"

The initial state of the Viper in DCS when the jet is either powered up from a cold
start or running following a hot start should match these requirements.

## MFD Formats

Each MFD on the Viper can display one of three formats (e.g., FCR, TGP, HSD) that are
selected by OSB 12, 13, and 14 on the MFD. The formats are tied to the current master
mode (NAV, AA, and AG) along with the dogfight modes (DOGFIGHT and MSL OVRD) that the
HOTAS DGFT switch selects. DCSWE maps four unique MFD setups to avionics modes as
follows,

- NAV master mode
- AG master mode (via ICP AG button)
- AA master mode (via ICP AA button), DGFT MSL OVRD override mode (via HOTAS DGFT switch)
- DGFT DOGFIGHT override mode (via HOTAS DGFT switch)

DCSWE allows per-mode selection of format sets to update. That is, you can update only
only AG while leaving the other setups in their default configuration.

For MFD format setup to work correctly, DCSWE expects the following initial conditions
in the Viper:

- Master mode should be NAV
- For all master modes that are to be updated, the current format selected on the left
  and right MFDs may not be whatever format is mapped to OSB 12
- The HOTAS DOGFIGHT switch `Cycle` command in DCS must be bound to the same hotkey
  specified in the DCSWE preferences
- DCS must be in the foreground so that it can recieve key presses

The initial state of the Viper in DCS when the jet is either powered up from a cold
start or running following a hot start should match these requirements.

When specifying the MFD setups, DCSWE provides an option to "only set MFD formats when
they differ from the default format assignments". This reduces the setup time by
reducing button presses; however, in this mode DCSWE is less able to handle deviations
from the default setups.

## CMDS Programs

There are five CMDS programs accessible through the UFC in the Viper: MAN 1 through 4
and the "Panic" program. Each program includes parameters for both chaff and flare
countermeasures that specify burst quantity, burst interval, salvo quantity, and salvo
interval to use when the corresponding program is triggered through the CMDS controls.

DCSWE allows any combination of the five programs to be changed from the default setup
in the jet.

For CMDS program setup to work correctly, DCSWE expects the following initial
conditions in the Viper:

- CMDS Chaff program 1 should be selected in the CMDS CHAFF DED page.
- CMDS Flare program 1 should be selected in the CMDS FLARE DED page.

The initial state of the Viper in DCS when the jet is either powered up from a cold
start or running following a hot start should match these requirements.

When specifying the CMDS programs, DCSWE provides an option to "only set CMDS program
parameters when they differ from the default parameters". This reduces the setup time by
reducing button presses; however, in this mode DCSWE is less able to handle deviations
from the default setups.

## Bullseye Setup

The avionics setup can specify either "ownship bullseye" or "steering cue" modes for the
FCR and HSD MFD formats.

## JHMCS Setup

The avionics setup can specify JHMCS setup parameters including blanking, RWR display,
and declutter level.
