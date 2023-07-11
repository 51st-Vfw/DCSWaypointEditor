'''
*
*  logger.py: Logging support
*
*  Copyright (C) 2020 Santi871
*  Copyright (C) 2021-23 twillis/ilominar
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

import logging
import os

from sys import stdout


def trim_logfile(header):
    if os.path.getsize("log.txt") > (64 * 1024):
        with open("log.txt", "r") as fh:
            logfile = fh.readlines()
        with open("log.txt", "w+") as fh:
            is_trimming = True
            for line in logfile[1:]:
                if is_trimming and line.find(header) != -1:
                    is_trimming = False
                if not is_trimming and len(line.strip()) > 0:
                    fh.write(line)

def get_logger(name):
    logger = logging.getLogger(name)
    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s:%(name)s: %(levelname)s - %(message)s')
    s_handler = logging.StreamHandler(stdout)
    s_handler.setFormatter(formatter)
    f_handler = logging.FileHandler("log.txt", encoding="utf-8")
    f_handler.setFormatter(formatter)
    logger.addHandler(f_handler)
    logger.addHandler(s_handler)
    logger.setLevel(logging.DEBUG)

    return logger
