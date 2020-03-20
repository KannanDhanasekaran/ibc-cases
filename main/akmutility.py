#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 18 2019

@author: Kannan
"""

import os.path
import sys
from configparser import ConfigParser
from datetime import datetime
import akmlogging

#print(sys.path)

# Get Logger
logger = akmlogging.getLoggerconfig()

# Parser for property file
parser = ConfigParser()
parser.read('..//config//akm.config')

# Source
SOURCE_NCLT = parser.get('source' , 'source_nclt')
SOURCE_NCLAT = parser.get('source' , 'source_nclat')
SOURCE_SUPREME = parser.get('source' , 'source_supreme')

# Extract PDF PATH
PDF_PATH_NCLT = parser.get('path', 'pdf_output_path_nclt')
PDF_PATH_NCLAT = parser.get('path', 'pdf_output_path_nclat')
PDF_PATH_SUPREME = parser.get('path', 'pdf_output_path_supreme')

# Get String with repeated characters
def getStringWithThis(thischar):
    return thischar * 143

# Format Date
def formatdate_dmy(formatstring):
    return datetime.strptime(formatstring, '%d-%m-%Y').date()

# Format Date
def formatdate_ymd(formatstring):
    return datetime.strptime(formatstring, '%Y-%m-%d').date()

def formatdate_dmonthyear(formatstring):
    formatdatestring = formatstring[0:2:] + formatstring[4::]
    return datetime.strptime(formatdatestring, '%d %B, %Y').date()

def formatdate_d_month_year(formatstring):
    return datetime.strptime(formatstring, '%d %B %Y').date()

def formatdate_dmonyear(formatstring):
    return datetime.strptime(formatstring, '%d %b, %Y').date()

def formatdate_dmonyearwithoutspace(formatstring):
    return datetime.strptime(formatstring, '%d%b%Y').date()

# Format ' String
def format_single_quote(field):
    if "'" in field:
        field = field.replace("'", "''")
    return field

#Format newLine , carriage return
def format_newLineCarriageReturn(field):
    return field.replace('\n', ' ').replace('\r', '')

# Set up - Download Dir
def setup_download_dir(OUTPUT_PATH):
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    else:
        logger.info(" Output Directory "+OUTPUT_PATH + "already exists!")

# Get Output Path
def getjudgementoutputpath(input):
    switcher = {
        SOURCE_NCLT: PDF_PATH_NCLT,
        SOURCE_NCLAT : PDF_PATH_NCLAT,
        SOURCE_SUPREME: PDF_PATH_SUPREME,
        }
    return switcher.get(input, "Invalid Judicial Body")

# Get JudicialBodies
def getJudicialBodiesList():
    return parser.get('judicial', 'judicialbodies').split(':')

#Get BenchList
def getBenchList():
    return parser.get('bench', 'benches').split(':')
