#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 18 2019

@author: Kannan
"""

import sys
import traceback
from configparser import ConfigParser

import akmlogging
import akmutility

# Get Logger
logger = akmlogging.getLoggerconfig()

# Parser for property file
parser = ConfigParser()
parser.read('..//config//akm.config')

# Extract SQL Query syntax
SQL_JUDGEMENT_LASTUPDATED_RECORD = parser.get('sql', 'judgement_lastupdated_record')
SQL_JUDGEMENT_UPDATE_VALIDFILE = parser.get('sql', 'judgement_update_file_status')
SQL_JUDGEMENT_UPDATE_INVALIDFILE = parser.get('sql', 'judgement_update_file_status_invalid')

SQL_JUDGEMENT_FETCH_LINKS = parser.get('sql', 'judgment_fetch_links')
SQL_JUDGEMENTS = parser.get('sql', 'insertjudgments_sql')
SQL_JUDGEMENTS_FILE_NAMES = parser.get('sql', 'judgements_fetch_file_names')
SQL_JUDGEMENTS_FETCH_EXISTING_FILE_NAMES = parser.get('sql', 'judgements_fetch_existing_file_names')
SQL_JUDGEMENT_FROM_DATE = parser.get('sql', 'judgements_fromDate')

# SQL Query - Select Last Updated Record in IBBI_WEB_MASTER_DATA
def getlastupdatedjudgementrecord(BENCH, SOURCE, CURSOR):
        # Prepare SQL query to Fetch Last Updated Record
    sql = SQL_JUDGEMENT_LASTUPDATED_RECORD
    val = (SOURCE, BENCH, SOURCE, BENCH)
    try:
        # Execute the SQL command
        CURSOR.execute(sql, val)
        # Fetch Record
        result = CURSOR.fetchone()
        return result
    except:
        # Rollback in case there is any error
        logger.error('Error in Method - getlastupdatedjudgementrecord() --> ' + sql)
        logger.error(traceback.print_exc(file=sys.stdout))

# SQL Query - Select Links To download files
def getjudgementlinkstodownload(SOURCE, BENCH_COURT, CURSOR):
    sql = SQL_JUDGEMENT_FETCH_LINKS
    val = (SOURCE, BENCH_COURT)
    try:
        # Execute the SQL command
        CURSOR.execute(sql, val)
        # Fetch Record
        results = CURSOR.fetchall()
        return results
    except:
        # Rollback in case there is any error
        logger.error('Error in Method getjudgementlinkstodownload() --> ' + sql)
        logger.error(traceback.print_exc(file=sys.stdout))


# SQL Query - Update Valid File Status
def updatejudgementfilestatus(val, valid_flag, CURSOR, MY_DB):
    # Prepare SQL query to update file status
    if bool(valid_flag):
        sql = SQL_JUDGEMENT_UPDATE_VALIDFILE
    else:
        sql = SQL_JUDGEMENT_UPDATE_INVALIDFILE
    try:
        # Execute the SQL command
        CURSOR.execute(sql, val)
        MY_DB.commit()
    except:
        # Rollback in case there is any error
        logger.error('Error in Method - updatejudgementfilestatus --> ' + sql)
        logger.error(traceback.print_exc(file=sys.stdout))
        MY_DB.rollback()


#SQL Query - Select Links To download files
def checkIfJudgementAlreadyExists(caseNo, petitionerName, judgementDateObj, BENCH, SOURCE, CURSOR):
    sql = SQL_JUDGEMENTS_FILE_NAMES
    val = (caseNo, petitionerName, judgementDateObj, BENCH, SOURCE)
    try:
        # Execute the SQL command
        CURSOR.execute(sql, val)
        # Fetch Record
        results = CURSOR.fetchall()
        return results
    except:
        # Rollback in case there is any error
        logger.error('Error in Method checkIfJudgementAlreadyExists() --> ' + sql)
        logger.error(traceback.print_exc(file=sys.stdout))

#SQL Query - To Check Duplicate File Records
def checkifJudgementFileExists(fileName, SOURCE, CURSOR):
    sql = SQL_JUDGEMENTS_FETCH_EXISTING_FILE_NAMES
    val = (fileName, SOURCE)
    try:
        # Execute the SQL command
        CURSOR.execute(sql, val)
        # Fetch Record
        results = CURSOR.fetchall()
        return results
    except:
        # Rollback in case there is any error
        logger.error('Error in Method checkifJudgementFileExists --> ' + sql)
        logger.error(traceback.print_exc(file=sys.stdout))

# SQL Query - Insert - IBBI_WEB_MASTERDATA - PA Information
def insert_judgements(caseNo, petitionerName, judgementDateObj, pdf_link, BENCH, fileName, SOURCE, MY_DB, CURSOR):
    # Prepare SQL query to INSERT a record into the database.
    sql = SQL_JUDGEMENTS.format(caseNo, petitionerName, judgementDateObj, pdf_link, BENCH, fileName, SOURCE, MY_DB, CURSOR)
    # print(sql)
    try:
        # Execute the SQL command
        CURSOR.execute(sql)
        # Commit your changes in the database
        MY_DB.commit()
    except:
        # Rollback in case there is any error
        logger.error('Error in SQL --> ' + sql)
        logger.error(traceback.print_exc(file=sys.stdout))
        MY_DB.rollback()

# Get Judgement From Date
def getJudgementFromDate(BENCH, SOURCE, CURSOR):
    # Prepare SQL query to Fetch Last Updated Record
    sql = SQL_JUDGEMENT_FROM_DATE
    val = (SOURCE, BENCH)
    try:
        # Execute the SQL command
        CURSOR.execute(sql, val)
        # Fetch Record
        result = CURSOR.fetchone()
        return result
    except:
        # Rollback in case there is any error
        logger.error('Error in Method - getJudgementFromDate() --> ' + sql)
        logger.error(traceback.print_exc(file=sys.stdout))
