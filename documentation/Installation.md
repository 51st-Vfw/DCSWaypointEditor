# Installation and Setup

Installation and setup of the DCS Waypoint Editor (DCSWE) is straight-forward and
requires the installation of several supporting software packages.

## Installing Supporting Software

DCSWE is written in `python` and requires a Python runtime to be installed on the
system. In addition, DCSWE uses
[DCS-BIOS](https://github.com/DCSFlightpanels/dcs-bios)
and
[Google Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
to support its operation. DCSWE uses DCS-BIOS to interact with controls in a DCS
clickable cockpit in order to set up the jet according to user specifications.
DCSWE uses Google Tesseract to help capture coordinates from the DCS F10 map (see
[DCSWE & DCS](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/DCSWE_DCS.md)).

> **NOTE:** There are multiple versions of DCS-BIOS available on the Internet. DCSWE
> requires the DCSFlightpanels version linked above; it is not compatible with the
> HUB or other versions of DCS-BIOS.

If you do not intend to capture waypoint coordinates from the DCS F10 map with DCSWE, you
can skip installing Google Tesseract. DCS-BIOS is critical as, without it, DCSWE cannot
interact with the aircraft to update settings.

Installation instructions for
[python](https://www.python.org/ftp/python/3.9.5/python-3.9.5-amd64.exe),
[DCS-BIOS](https://github.com/DCSFlightpanels/dcs-bios),
and
[Google Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
are available at the links. Once you have installed this software, logout and reboot
to ensure path changes are updated. Next, you can install DCSWE itself.

## Installing DCSWE

You can install DCSWE from either a `.zip` archive that contains a pre-built archive or
by building the archive yourself directly from source.

### Using the Pre-Built Archive

> **NOTE:** For Most users, using the pre-built archive is the easiest way to install
> DCSWE.

A `.zip` archive with a pre-built archive for DCSWE is available in the
[release area](https://github.com/51st-Vfw/DCSWaypointEditor/releases)
on the GitHub DCSWE page. To install DCSWE from the archive, simply download the
`dcs_wp_editor.zip` archive from the GitHub release and unzip the archive to your
disk. Unzipping the archive will build a `dcs_wp_editor` directory that contains all
the files necessary for DCSWE. You may rename this directory and move it where ever
you please. It does not need to be located in any specific directory.

> **NOTE:** Do not distrub or move any of the files *within* the `dcs_wp_editor`
> folder from the package. For proper operation, the contents of this folder must
> remain intact.

You may want to create a shortcut to the `dcs_wp_editor.exe` executable to more easily
launch DCSWE.

### Building from Source

An source code package for DCSWE is available in the
[release area](https://github.com/51st-Vfw/DCSWaypointEditor/releases)
on the GitHub DCSWE page. Unpack the source code package to the directory you would
like the source code to reside in. To build the package, you will begin by opening
a shell and moving into the top-level directory of the source tree. From there, you
run the `pip` and `pyinstaller` commands,

```
pip install -r requirements.txt
pyinstaller -w dcs_wp_editor.py
```

These will install required pypthon packages and create a distribution in the
`dist\dcs_wp_editor` subdirectory at the root of the source tree. After finishing the
build, copy the entire `data\` subdirectory from the root of the source tree into the
distribution directory `dist\dcs_wp_editor`.

The `dist\dcs_wp_editor` directory contains the DCSWE distribution and can be moved
and renamed as you see fit. You may want to create a shortcut to the `dcs_wp_editor.exe`
executable in this directory to more easily launch DCSWE.

If you see a "Failed to execute script" when running the `dcs_wp_editor.exe` executable
in `dist\dcs_wp_editor`, there are two potential fixes.

First, in the `dcs_wp_editor.spec` file (this should be in the same directory as
`dcs_wp_editor.py` in the source tree), change the `hiddenimports` line to:

```
hiddenimports=['pkg_resources']
```

Then re-run `pyinstaller` on `dcs_wp_editor.spec` (*not* the Python file as shown
above, note that if you run `pyinstaller` on the python file, the `.spec` file will be
over-written).

Second, you can add `--hidden-import` to the `pyinstaller` command line by using this
instead of the invocation above,

```
pyinstaller -w --hidden-import pkg_resources dcs_wp_editor.py
```

In this case, you should not need to change the `.spec` file.

## Setting Up DCSWE

When you run DCSWE for the first time, it will ask if it is OK for the program to
create some files in a `DCSWE` directory DCSWE will create in your `Documents`
directory at

```
{HOME}\Documents\DCSWE\
```

Where `{HOME}` is your Windows home directory. You may accept or reject this request.

> **NOTE:** If you do not permit DCSWE to create files in the `Documments`
> directories, it will instead create the necessary files in the DCSWE directory
> itself. Generally, it is a good idea to allow DCSWE to write to `Documents`.

The files DCSWE creates include,

- Settings file that contains the current preferences and settings for DCSWE.
- Profiles database file that contains the current profiles and setups DCSWE knows
  about.
- Screen captures useful for debugging DCS F10 coordinate capture (when the
  capture debug mode is enabled).

In addition, DCSWE will create a `log.txt` file in the DCSWE directory that provides
log output that can be useful when reporting bugs.

On the first launch, DCSWE will presenting the preferences UI to allow you to setup
the DCSWE preferences. The values will be set to their default values and you may
change them based on your setup. Generally, there are three preferences that are
important to set up at this point,

- *DCS Saved Games Directory:* Locates the directory where DCS keeps its "saved game"
  hierarchy for the DCS installation you want DCSWE to work with. Typically, this is
  something like `{HOME}\Saved Games\DCS.openbeta`.
- *Tesseract Executable:* Locates the `tesseract.exe` executable installed as part of
  the tesseract installation.
- *F-16 HOTAS DOGFIGHT Cycle:* Specifies the keybind for the `Cycle` command on the
  HOTAS DGFT switch if you are using the avionics setup functionality for the Viper.
  See the discussion of
  [avionics setup](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Avionics_Setup.md)
  for more information.

See the discussion of
[preferences](https://github.com/51st-Vfw/DCSWaypointEditor/blob/master/documentation/Preferences.md)
for further details on the preferences.

## Running DCSWE

Depending on how you have setup your Windows system, DCSWE may need administrator
privilages for the hotkeys to function correctly. If you find yourself unable to capture
coordinates or load a profile using the hotkeys you set up in the preferences, try
running DCSWE as an administrator.
