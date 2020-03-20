#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Sun Nov 17 23:20:33 2019

@author: Kannan
"""
import os
import sys
import time
import traceback
import urllib
import urllib3
from urllib3.exceptions import ReadTimeoutError
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
from functools import partial
import akmlogging
import dbconfiguration
import dbpersistence
import akmutility
from datetime import datetime

# Get Logger
import requests

logger = akmlogging.getLoggerconfig()

# Parser for property file
parser = ConfigParser()
parser.read('..//config//akm.config')

VALID_FLAG = 1
INVALID_FLAG = 0
updateArr_valid = []
updateArr_invalid = []

# PDF
PDF_EXTN = parser.get('path', 'pdf_extn')

# Get DB connection
MY_DB = dbconfiguration.getDB()
#logger.info('Establishing Database Connection.. ' + str(MY_DB))

# Prepare a cursor object using cursor() method
CURSOR = MY_DB.cursor()

# Get Links and File Names Function
def getlinksandfilenamesforjudgements(SOURCE, BENCH_COURT):
    fileNames = dbpersistence.getjudgementlinkstodownload(SOURCE, BENCH_COURT, CURSOR)
    return fileNames

# Download pdf and update file status
def download_url_update_status(result):
    id = str(result[0])
    file_name = str(result[1])
    url = str(result[2])
    if not url.strip():
        logger.info("Invalid URL --> "+url)
        # Update DB - IS_VALID_LINK = N
        val = (id,)
        updateArr_invalid.append(val)
        #dbpersistence.updatefilestatus(val, INVALID_FLAG, CURSOR, MY_DB)
        return
    else:
        url_d = url.replace("'", "")
        if url_d.startswith("("):
            url_d = url_d[1:]
        if url_d.endswith(")"):
            url_d = url_d[:len(url_d) - 1]
        if url_d.endswith(","):
            url_d = url_d[:len(url_d) - 1]
        file_name_d = getDirStructurePath(result[3], MOD_PDF_PATH) + file_name
        #print(file_name_d)
        #val = (file_name, id)
        val = (id,)
        #print(url_d)
        #print("Getting request....")
        r = requests.get(url_d, verify = False, stream=True)
        if r.status_code == requests.codes.ok:
            #print("valid url")
            with open(file_name_d, 'wb') as f:
                for data in r:
                    f.write(data)
                #dbpersistence.updatefilestatus(val, VALID_FLAG, CURSOR, MY_DB)
                if not os.path.exists(file_name_d):
                    logger.error("Unable to write to "+file_name_d)
                else:
                    updateArr_valid.append(val)
        else:
            #print("invalid url")
            logger.info("Invalid URL --> " + url_d)
            # Update DB - IS_VALID_LINK = N
            val = (id,)
            #dbpersistence.updatefilestatus(val, INVALID_FLAG, CURSOR, MY_DB)
            updateArr_invalid.append(val)
    return url_d


def getFileNamesFromDB(source):
    results = dbpersistence.getFileNamesFromDB(source, CURSOR)
    return results


def getDirStructurePath(judgementDate, MOD_PDF_PATH):
    dateValue = judgementDate.strftime('%Y%m%d')
    path = MOD_PDF_PATH + dateValue + '/'
    return path

def createDirStructure(results, MOD_PDF_PATH):
    for result in results:
        dirStructure = getDirStructurePath(result[3], MOD_PDF_PATH)
        akmutility.setup_download_dir(dirStructure)

if __name__ == "__main__":
    benchCourtList = akmutility.getBenchList()
    judicialBodiesList = akmutility.getJudicialBodiesList()
    # current date and time
    now = datetime.now()
    CURRENT_DATE_DIR = now.strftime("%Y%m%d")
    for SOURCE in judicialBodiesList:
        for BENCH_COURT in benchCourtList:
            #BENCH_COURT = BENCH.replace('Bench', '').replace(' ', '')
            logger.info(akmutility.getStringWithThis("*"))
            logger.info(f'JUDGEMENTS DATA DOWNLOAD from {SOURCE} for Bench {BENCH_COURT} STARTED !')
            START_TIME = time.time()
            PDF_PATH = akmutility.getjudgementoutputpath(SOURCE)
            MOD_PDF_PATH = PDF_PATH  + "/"+ BENCH_COURT + "/"
            try:
                results = getlinksandfilenamesforjudgements(SOURCE, BENCH_COURT)
                #print(results)
                if len(results) > 0:
                    createDirStructure(results, MOD_PDF_PATH)
                #fileNames = getFileNamesFromDB(source)
                with ThreadPoolExecutor() as executor:
                # Create a new partially applied function that stores the directory argument.
                # This allows the download_link function that normally takes two
                # arguments to work with the map function that expects a function of a
                # single argument.
                    fn = partial(download_url_update_status)
                    # Executes fn concurrently using threads on the links iterable. The
                    # timeout is for the entire process, not a single call, so downloading
                    # all images must complete within 30 seconds.
                    executor.map(fn, results, timeout=30)
            except:
                # Rollback in case there is any error
                traceback.print_exc(file=sys.stdout)
                MY_DB.rollback()

            if len(updateArr_valid) > 0 or len(updateArr_invalid) > 0:
                logger.info(f"Updating Database - {SOURCE}............................................................... ")
                for value in updateArr_valid:
                    dbpersistence.updatejudgementfilestatus(value, VALID_FLAG, CURSOR, MY_DB)

                for value in updateArr_invalid:
                    dbpersistence.updatejudgementfilestatus(value, INVALID_FLAG, CURSOR, MY_DB)
                logger.info(f"Database Updated - {SOURCE}! ")


            logger.info(f'JUDGEMENTS DOWNLOAD for {BENCH_COURT} from {SOURCE} COMPLETED!')
            logger.info(akmutility.getStringWithThis("*"))
    END_TIME = time.time()
    logger.info(f"Time taken to download the Judgements from {SOURCE} and update database is {END_TIME - START_TIME} seconds ")
    logger.info(akmutility.getStringWithThis("*"))

MY_DB.close()
CURSOR.close()

