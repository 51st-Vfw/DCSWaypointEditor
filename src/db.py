'''
*
*  db.py: DCS Waypoint Editor profile database
*
*  Copyright (C) 2020 Santi871
*  Copyright (C) 2021-22 twillis/ilominar
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

from peewee import CharField, IntegerField, IntegrityError, SqliteDatabase
from playhouse.migrate import SqliteMigrator, migrate

from src.db_models import ProfileModel, WaypointModel, SequenceModel, AvionicsSetupModel, db
from src.logger import get_logger


class DatabaseInterface:
    def __init__(self, db_name):
        self.logger = get_logger(__name__)
        self.db_version = 1

        db.init(db_name)
        db.connect()
        db.create_tables([ProfileModel, WaypointModel, SequenceModel, AvionicsSetupModel])
        self.logger.debug(f"Connected to database {db_name}")

        migrator = SqliteMigrator(db)
        try:
            for metadata in db.get_columns('ProfileModel'):
                if metadata.name == 'av_setup_name':
                    #
                    # db v.2 adds "av_setup_name" column to "ProfileModel" table.
                    #
                    self.db_version = 2
                    break
            for metadata in db.get_columns('WaypointModel'):
                if self.db_version == 2 and metadata.name == 'is_set_cur':
                    #
                    # db v.3 adds "is_set_cur" column to "WaypointModel" table.
                    #
                    self.db_version = 3
                    break
            for metadata in db.get_columns('AvionicsSetupModel'):
                if self.db_version == 3 and metadata.name == 'f16_cmds_setup_p1':
                    #
                    # db v.4 adds "f16_cmds_setup_p<x>" columns to "AvionicsSetupModel" table.
                    #
                    self.db_version = 4
                    break
            for metadata in db.get_columns('AvionicsSetupModel'):
                if self.db_version == 4 and metadata.name == 'f16_bulls_setup':
                    #
                    # db v.5 adds "f16_bulls_setup" and "f16_jhmcs_setup" columns to
                    # "AvionicsSetupModel" table.
                    #
                    self.db_version = 5
                    break
            for metadata in db.get_columns('AvionicsSetupModel'):
                if self.db_version == 5 and metadata.name == 'f16_cmds_setup_p6':
                    #
                    # db v.6 adds "f16_cmds_setup_p6" column to "AvionicsSetupModel" table.
                    #
                    self.db_version = 6
                    break
            for metadata in db.get_columns('AvionicsSetupModel'):
                if self.db_version == 6 and metadata.name == 'f16_mfd_setup_opt':
                    #
                    # db v.7 adds "f16_mfd_setup_opt" column to "AvionicsSetupModel" table.
                    #
                    self.db_version = 7
                    break

            for metadata in db.get_columns('AvionicsSetupModel'):
                if self.db_version == 7 and metadata.name == 'f16_cmds_setup_opt':
                    #
                    # db v.8 adds "f16_cmds_setup_opt" column to "AvionicsSetupModel" table.
                    #
                    self.db_version = 8
                    break

            if self.db_version == 1:
                avionics_setup_field = CharField(null=True, unique=False)
                with db.atomic():
                    migrate(
                        migrator.add_column('ProfileModel', 'av_setup_name', avionics_setup_field)
                    )
                self.db_version = 2
                self.logger.debug(f"Migrated database {db_name} to v{self.db_version}")
            if self.db_version == 2:
                is_init_field = IntegerField(default=False)
                with db.atomic():
                    migrate(
                        migrator.add_column('WaypointModel', 'is_set_cur', is_init_field)
                    )
                self.db_version = 3
                self.logger.debug(f"Migrated database {db_name} to v{self.db_version}")
            if self.db_version == 3:
                is_init_field = CharField(null=True, default=None)
                with db.atomic():
                    migrate(
                        migrator.add_column('AvionicsSetupModel', 'f16_cmds_setup_p1', is_init_field),
                        migrator.add_column('AvionicsSetupModel', 'f16_cmds_setup_p2', is_init_field),
                        migrator.add_column('AvionicsSetupModel', 'f16_cmds_setup_p3', is_init_field),
                        migrator.add_column('AvionicsSetupModel', 'f16_cmds_setup_p4', is_init_field),
                        migrator.add_column('AvionicsSetupModel', 'f16_cmds_setup_p5', is_init_field)
                    )
                self.db_version = 4
                self.logger.debug(f"Migrated database {db_name} to v{self.db_version}")
            if self.db_version == 4:
                is_init_field = CharField(null=True, default=None)
                with db.atomic():
                    migrate(
                        migrator.add_column('AvionicsSetupModel', 'f16_bulls_setup', is_init_field),
                        migrator.add_column('AvionicsSetupModel', 'f16_jhmcs_setup', is_init_field)
                    )
                self.db_version = 5
                self.logger.debug(f"Migrated database {db_name} to v{self.db_version}")
            if self.db_version == 5:
                is_init_field = CharField(null=True, default=None)
                with db.atomic():
                    migrate(
                        migrator.add_column('AvionicsSetupModel', 'f16_cmds_setup_p6', is_init_field),
                    )
                self.db_version = 6
                self.logger.debug(f"Migrated database {db_name} to v{self.db_version}")
            if self.db_version == 6:
                is_init_field = IntegerField(default=False)
                with db.atomic():
                    migrate(
                        migrator.add_column('AvionicsSetupModel', 'f16_mfd_setup_opt', is_init_field),
                    )
                self.db_version = 7
                self.logger.debug(f"Migrated database {db_name} to v{self.db_version}")
            if self.db_version == 7:
                is_init_field = IntegerField(default=False)
                with db.atomic():
                    migrate(
                        migrator.add_column('AvionicsSetupModel', 'f16_cmds_setup_opt', is_init_field),
                    )
                self.db_version = 8
                self.logger.debug(f"Migrated database {db_name} to v{self.db_version}")

            self.logger.debug(f"Database {db_name} is v{self.db_version}")

        except Exception as e:
            self.logger.error(f"Database migration fails, {e}")
            raise e

    @staticmethod
    def close():
        db.close()
