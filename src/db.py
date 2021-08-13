'''
*
*  db.py: DCS Waypoint Editor profile database
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
                    # db v.2 adds "viper_setup" column to "ProfileModel" table.
                    #
                    self.db_version = 2
            for metadata in db.get_columns('WaypointModel'):
                if self.db_version == 2 and metadata.name == 'is_set_cur':
                    #
                    # db v.3 adds "is_set_cur" column to "WaypointModel" table.
                    #
                    self.db_version = 3

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

        except Exception as e:
            self.logger.error(f"Database migration fails, {e}")
            raise e

    @staticmethod
    def close():
        db.close()
