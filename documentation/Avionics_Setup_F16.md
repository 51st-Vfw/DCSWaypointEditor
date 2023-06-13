# Avionics Setup: F-16C Viper

DCC Waypoint Editor (DCSWE) supports avionics setup for the F-16C Viper. The following
state, in addition to
[steerpoints](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Waypoint_Setup.md),
can be set up:

- TACAN yardstick
- MFD formats for use on the left and right MFDs in NAV, AA, AG, and DGFT master modes
- CMDS programs for chaff and flares
- Bullseye display on FCR and HSD MFD formats
- JHMCS setup

As with waypoint entry, it is important to minimize interactions with the jet while
DCSWE is driving the cockpit switches.

[Avionics Setup](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Avionics_Setup.md)
describes the elements of the avionics setup user interface that are common to all
airframes. This section will focus on the user interface specific to the F-16C.

## Related DCSWE Preferences

There are three preferences that control the behavior of the avionics setup functionality
for the Viper (see
[Preferences](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Preferences.md)
for further details):

- *Default Avionics Setup:* From the `Miscellaneous` tab specifies the default avionics
  setup to use when creating new profiles. The setup "DCS Default" corresponds to the
  default setup of the jet in DCS in cold or hot starts.
- *Use When Setup Unknown:* From the `Miscellaneous` tab causes DCSWE to use the default
  avionics setup in situations where it does not have information on the avionics setup.
  For example, if this is set, when loading a mission from a CombatFlite export file
  will use the specified default avionics setup. When not set, DCSWE will not change
  avionics setup if it does not have information on the desired setup (i.e., it behaves
  as if the default were "DCS Default")
- *F-16 HOTAS / DOGFIGHT Cycle:* From the `Keyboard` tab specifies the keybind for the
  `Cycle` command on the HOTAS DOGFIGHT switch in the Viper, the keybind should use at
  least one of `shift`, `alt`, or `ctrl`. The keybind should be specified keeping in
  mind that DCS uses specific modifiers (left or right `shift`, for example).

These can be set throught the
[DCSWE Preferences](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Preferences.md),
strangely enough. Note that the
`DOGFIGHT Cycle` hotkey will need to also be set up through the control options in DCS
(specifically, see the HOTAS section in the "F-16C Sim" controls).

## MFD Formats

Each MFD in the Viper can display one of three formats (e.g., FCR, TGP, HSD) that are
selected by OSB 12, 13, and 14 on the MFD. The formats are tied to the current master
mode (NAV, AA, and AG) along with the dogfight modes (DOGFIGHT and MSL OVRD) that the
HOTAS DOGFIGHT switch selects. DCSWE maps four unique MFD setups to avionics modes as
follows,

1. NAV master mode
2. AG master mode (via ICP AG button)
3. AA master mode (via ICP AA button), DGFT MSL OVRD override mode (via HOTAS
   DOGFIGHT switch)
4. DGFT DOGFIGHT override mode (via HOTAS DOGFIGHT switch)

DCSWE allows per-mode selection of format sets to update. That is, you can update only
only AG while leaving the other setups in their default configuration.

The MFD formats are set up through the "`MFD Formats`" tab in the interface.

![F-16C Avionics Setup: MFD Formats](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/images/Avionics_F16_MFD.jpg)

Each section of the tab specifies a set of up to three formats to use for the left and
right MFDs. The setups are broken down by avionics modes as listed above. Selecting the
"Reconfigure..." checkbox at left causes DCSWE to update the formats when the avionics
setup is loaded into the jet. In this figure, the avionics are set up such that, in
air-to-ground mode, the left MFD displays FCS/HAD/WPN formats while the right MFD
displays SMS/HSD/TGP formats.

When specifying the MFD setups, DCSWE provides an option to "only set MFD formats when
they differ from the default format assignments". This reduces the setup time by
reducing button presses; however, in this mode DCSWE is less able to handle deviations
from the default setups.

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

The TACAN yardstick is set up through the "`TACAN`" tab in the interface.

![F-16C Avionics Setup: TACAN](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/images/Avionics_F16_TACAN.jpg)

To include the TACAN in the avionics setup, the check box next to "Setup TACAN yardstick
at:" must be selected. The remainder of the controls should be set to the desired
configuration.

For TACAN setup to work correctly, DCSWE expects the following initial conditions in
the Viper:

- TACAN band should be "X"
- TACAN operation mode should be "REC"
- EHSI mode should be "NAV"

The initial state of the Viper in DCS when the jet is either powered up from a cold
start or running following a hot start should match these requirements.

## CMDS Programs

There are five CMDS programs accessible through the UFC in the Viper: MAN 1 through 4
and the "Panic" program. Each program includes parameters for both chaff and flare
countermeasures that specify burst quantity, burst interval, salvo quantity, and salvo
interval to use when the corresponding program is triggered through the CMDS controls.

DCSWE allows any combination of the five programs to be changed from the default setup
in the jet.

The CMDS programs are set up through the "`CMDS`" tab in the interface.

![F-16C Avionics Setup: CMDS](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/images/Avionics_F16_CMDS.jpg)

The parameters for each chaff or flare program include,

- *Burst Quantity:* Number of countermeasures released per burst, between 1 and 99.
- *Burst Interval:* Delay in seconds between bursts, between 0.020 and 10.000.
- *Salvo Quantity:* Number of bursts per salvo, between 1 and 99.
- *Salvo Interval:* Delay in seconds between salvos, 0.50 and 150.00.

These parameters are programmed into the jet when "Change this program" is selected.
Note that both chaff and flares are set for a program; DCSWE does not support only
updating the chaff part of the program.

When specifying the CMDS programs, DCSWE provides an option to "only set CMDS program
parameters when they differ from the default parameters". This reduces the setup time by
reducing button presses; however, in this mode DCSWE is less able to handle deviations
from the default setups.

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

## Miscellaneous

Finally, you can specify miscellaneous settings such as the bullseye and JHMCS
parameters for the avionics setup.

Miscellaneous items are set up through the "`Miscellaneous`" tab in the interface.

![F-16C Avionics Setup: Miscellaneous](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/images/Avionics_F16_Misc.jpg)

For bullseye, the avionics setup can specify either "ownship bullseye" or "steering cue"
modes for any use of the FCR and HSD MFD formats.

For JHMCS, the avionics setup can specify JHMCS setup parameters including blanking,
RWR display, and declutter level.
