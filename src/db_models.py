'''
*
*  db.py: DCS Waypoint Editor profile database models
*
*  Copyright (C) 2020 Santi871
*  Copyright (C) 2021 twillis/ilominar
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

from peewee import Model, IntegerField, CharField, ForeignKeyField, FloatField, SqliteDatabase


db = SqliteDatabase(None, pragmas={'foreign_keys': 1})


class BaseModel(Model):
    class Meta:
        database = db


class ProfileModel(BaseModel):
    name = CharField(unique=True)
    aircraft = CharField(unique=False)
    #
    # Field added in db v.2, v1.1.0-51stVFW and later
    #
    av_setup_name = CharField(null=True, unique=False)

    @staticmethod
    def list_all():
        return sorted(list(ProfileModel.select()), key=lambda profile: profile.name)

    @staticmethod
    def list_all_names():
        return [ profile.name for profile in ProfileModel.list_all() ]


class SequenceModel(BaseModel):
    identifier = IntegerField()
    profile = ForeignKeyField(ProfileModel, backref='sequences')


class WaypointModel(BaseModel):
    name = CharField(null=True, default="")
    latitude = FloatField()
    longitude = FloatField()
    elevation = IntegerField(default=0)
    profile = ForeignKeyField(ProfileModel, backref='waypoints')
    sequence = ForeignKeyField(SequenceModel, backref='waypoints', null=True)
    wp_type = CharField()
    station = IntegerField(default=0)
    #
    # Field added in db v.3, v1.2.0-51stVFW and later
    #
    is_set_cur = IntegerField(default=False)

# Model added in db v.2, v1.1.0-51stVFW and later
#
class AvionicsSetupModel(BaseModel):
    name = CharField(null=False, unique=True)

    # airframes supported: viper
    # 
    # CSV list of the format: "<channel>,<X|Y>,<L|W>" where <channel> is an integer on 1..63,
    # <X|Y> selects x-ray or yankee channel, and <L|W> specifies a role of lead or wingman.
    # With a wingman role, the channel entered into the jet is <channel> + 63.
    #
    # TODO: support other airframes?
    #
    tacan_yard = CharField(null=True, default=None)

    # airframes supported: viper
    #
    # CSV list of 6 integers corresponding to MFD OSBs L 14, L 13, L 12, R 14, R 13, R 12
    # (i.e., list[0] = L 14, list[1] = L 13, etc.). integers values are the OSB to push on
    # the format select page to select desired format.
    #
    f16_mfd_setup_nav = CharField(null=True, default=None)
    f16_mfd_setup_air = CharField(null=True, default=None)
    f16_mfd_setup_gnd = CharField(null=True, default=None)
    f16_mfd_setup_dog = CharField(null=True, default=None)

    # airframes supported: viper
    #
    # Fields added in db v.4, v1.3.0-51stVFW and later
    #
    # List of integers/floats corresponding to the CMDS program parameters. The strings
    # are of the format "<C>;<F>" where <C> and <F> are the chaff and flare programs,
    # respectively. Both <C> and <F> are of the form "<BQ>,<BI>,<SQ>,<SI>" where <BQ>
    # and <SQ> are integers on [0, 99], <BI> is a float on [0.020, 10.000] (the float
    # must have 3 digits right of decimal), and <SI> is a float on [0.50, 150.00] (the
    # float must have 2 digits right of decimal). None (empty string) indicates default.
    #
    f16_cmds_setup_p1 = CharField(null=True, default=None)
    f16_cmds_setup_p2 = CharField(null=True, default=None)
    f16_cmds_setup_p3 = CharField(null=True, default=None)
    f16_cmds_setup_p4 = CharField(null=True, default=None)
    f16_cmds_setup_p5 = CharField(null=True, default=None)

    # airframes supported: viper
    #
    # Fields added in db v.5, v1.4.0-51stVFW and later
    #
    # Bulls setup is a string where "0" indicates steering cue and "1" indicates ownship
    # bullseye FCR/HSD MFD setup.
    #
    # JHMCS setup is a a string of the form "<HUD>,<PIT>,<RWR>,<DEC>" where <HUD>, <PIT>,
    # and <RWR> are integers with 0 disabling and 1 enabling HUD block, cockpit block,
    # and RWR display, respectively and <DEC> is an integer on [0,2] indicating the
    # declutter level - 1.
    #
    # In both, None (empty string) indicates default setup.
    #
    f16_bulls_setup = CharField(null=True, default=None)
    f16_jhmcs_setup = CharField(null=True, default=None)

    # airframes supported: viper
    #
    # Fields added in db v.6, v1.5.0-51stVFW and later
    #
    # Format of this field is identical to the f16_cmds_setup_p? fields from db v.4
    # (see above).
    #
    f16_cmds_setup_p6 = CharField(null=True, default=None)

    # airframes supported: viper
    #
    # Fields added in db v.7, v1.6.0-51stVFW and later
    #
    # Selects optimized setup of MFD formats.
    #
    f16_mfd_setup_opt = IntegerField(default=False)

    @staticmethod
    def list_all():
        return sorted(list(AvionicsSetupModel.select()), key=lambda setup: setup.name)

    @staticmethod
    def list_all_names():
        return [ setup.name for setup in AvionicsSetupModel.list_all() ]
