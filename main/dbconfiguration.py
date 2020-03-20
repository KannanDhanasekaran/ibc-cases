#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 18 2019

@author: Kannan
"""

from configparser import ConfigParser
import mysql.connector  # library to connect to mysql

# Parser for property file
parser = ConfigParser()
parser.read('..//config//akm.config')

# Get DB Connection
def getDB():
    # database information
    MY_DB = mysql.connector.connect(
        host=parser.get('database_config', 'host'),
        user=parser.get('database_config', 'username'),
        passwd=parser.get('database_config', 'password'),
        database=parser.get('database_config', 'database'),
    )
    return MY_DB
