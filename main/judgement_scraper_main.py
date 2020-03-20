#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author: Kannan
"""
import re
import time
import sys
import traceback
from configparser import ConfigParser
import akmlogging
import dbpersistence
import requests  # library to load html data from url
from bs4 import BeautifulSoup  # library for webscraping

import akmutility
import dbconfiguration
from datetime import date

# Get Logger
import urllib3
from urllib3.exceptions import ReadTimeoutError
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = akmlogging.getLoggerconfig()

# Parser for property file
parser = ConfigParser()
parser.read('..//config//akm.config')

# Get DB connection
MY_DB = dbconfiguration.getDB()
# logger.info('Establishing Database Connection.. ' + str(MY_DB))

# Prepare a cursor object using cursor() method
CURSOR = MY_DB.cursor()

# Source - From where this data is being scrapped
# SOURCE = parser.get('source', 'source_cirp')

# Page to traverse from - To load delta value
DELTA_PAGE = int(parser.get('update', 'delta_from_page'))


# Page to traverse from - To load delta value
JUDGEMENT_FROM_DATE = parser.get('update', 'judgement_from_date')

# PDF
PDF_EXTN = parser.get('path', 'pdf_extn')
DUPLICATE_LABEL = '_D'


# Get SOUP Function
def getsoup(PAGE, MAIN_URL_TO_SCRAPE, flag):
    # Function to find Last Page
    URL_TO_SCRAPE = MAIN_URL_TO_SCRAPE + str(PAGE)
    retry = 0
    is_done = False
    max_retries = 10
    sleep_interval = 5
    while retry < max_retries and not is_done:
        try:
            logger.info("Scraping URL ---->" + URL_TO_SCRAPE)
            # Load html's plain data into a variable
            PLAIN_HTML_TEXT = requests.get(URL_TO_SCRAPE, verify=False)
            # parse the data
            SOUP = BeautifulSoup(PLAIN_HTML_TEXT.text, "html.parser")
            is_done = True
        except ReadTimeoutError:
            retry += 1
            time.sleep(sleep_interval)
    if not is_done:
        logger.error(URL_TO_SCRAPE + ' - could not be loaded')
    return SOUP


# Last Page Function
def getlastpage(SOUP):
    LAST_PAGE_URL = SOUP.find("li", {"pager-last last"})
    if LAST_PAGE_URL is None:
        logger.info("Only One page data is available")
        return 1
    LP_HREF = LAST_PAGE_URL.find('a').get('href')
    PAGE_INDEX = LP_HREF.find("&page=")
    LAST_PAGE = int(LP_HREF[PAGE_INDEX + 6:])
    logger.info("Last Page -> "+str(LAST_PAGE))
    return LAST_PAGE


# Get Field values
def checkIBCCases(basic_data_cells):
    caseNo = basic_data_cells[1].text.strip()
    if 'IB' in caseNo.upper():
        return True
    else:
        return False

# Get Field values
def getfieldvalues(basic_data_cells):
    caseNo = basic_data_cells[1].text.strip()
    if "'" in caseNo:
        caseNo = akmutility.format_single_quote(caseNo)
    petitionerName = basic_data_cells[2].text.strip()
    petitionerName = akmutility.format_newLineCarriageReturn(petitionerName)
    petitionerName = akmutility.format_single_quote(petitionerName)
    petitionerName = re.sub(r'\s+', ' ', petitionerName)
    judgementDate = basic_data_cells[3].text.strip()
    if len(judgementDate) > 0:
        judgementDateObj = akmutility.formatdate_dmy(judgementDate)
    else:
        judgementDateObj = ''
    pa_url = basic_data_cells[4].find('a').get('href')
    start = pa_url.find('https')
    end = pa_url.find('.pdf')
    pdf_link = pa_url[start:end + 4]
    #print("Case No - " + caseNo)
    #print("Petitioner Name - " + petitionerName)
    #print("Judgement Date - " + str(judgementDateObj))
    #print("PDF Link - " + pdf_link)
    return caseNo, petitionerName, judgementDateObj, pdf_link


# Get Key Values Function - @Return - (Date of Announcement + Last Date of Submission + Corp Debtor Name)
def getkeyvalues(basic_data_cells):
    caseNo = basic_data_cells[1].text.strip()
    petitionerName = basic_data_cells[2].text.strip()
    petitionerName = akmutility.format_newLineCarriageReturn(petitionerName)
    petitionerName = akmutility.format_single_quote(petitionerName)
    petitionerName = re.sub(r'\s+', ' ', petitionerName)
    judgementDate = basic_data_cells[3].text.strip()
    if len(judgementDate) > 0:
        judgementDateObj = akmutility.formatdate_dmy(judgementDate)
    else:
        judgementDateObj = ''
    keyValue = caseNo + petitionerName + str(judgementDateObj)
    #print("Key Value -> "+keyValue)
    return caseNo + petitionerName + str(judgementDateObj)


# Construct File Name
def constructFileName(caseNo, petitionerName, judgementDateObj, BENCH, SOURCE):
    bench = BENCH.replace('Bench', '').replace(' ','')
    #caseNo = caseNo.replace(' ', '').replace('\n','').replace('/','').replace('(','').replace(')','').replace('.',)
    caseNo = re.sub('\W+','', caseNo)
    caseNo = caseNo.replace('in', '').replace('IN', '').replace('In','').replace('of', '').replace('OF', '').replace('Of','').replace('WITH','').replace('with','').replace('No','').replace('NO','').replace('no','')
    caseNo = caseNo[:80]
    judgementDateObj = str(judgementDateObj).replace('-', '')
    fileName = caseNo + judgementDateObj +  bench + SOURCE
    fileName = fileName + PDF_EXTN
    #print(fileName)
    results = dbpersistence.checkIfJudgementAlreadyExists(caseNo, petitionerName, judgementDateObj, BENCH, SOURCE, CURSOR)
    if len(results) == 0:
        return fileName
    else:
        resultsFile = dbpersistence.checkifJudgementFileExists(fileName, SOURCE, CURSOR)
        duplicateIndex = []
        # print(results)
        for result in results:
            file_Name = result[0].replace(PDF_EXTN, '')
            index = file_Name.find(DUPLICATE_LABEL)
            if index == -1:
                duplicateIndex.append(0)
            else:
                indexfound = (int)(file_Name[index + 2:])
                duplicateIndex.append(indexfound)
        maxValue = max(duplicateIndex) + 1
        fileName = fileName + DUPLICATE_LABEL + str(maxValue) + PDF_EXTN
    return fileName


def dbInsert(basic_data_cells, BENCH, SOURCE):
        [caseNo, petitionerName, judgementDateObj, pdf_link]  = getfieldvalues(basic_data_cells)
        fileName = constructFileName(caseNo, petitionerName, judgementDateObj, BENCH, SOURCE)
        dbpersistence.insert_judgements(caseNo, petitionerName, judgementDateObj, pdf_link, BENCH, fileName, SOURCE, MY_DB, CURSOR)

# Constructing the date till which the judgements need to be extracted
def constructDate(date_object):
    day = "0" + str(date_object.day)
    dayString = day[-2:]
    month = "0" + str(date_object.month)
    monthString = month[-2:]
    year = str(date_object.year)
    yearString = year[-2:]
    dateString = dayString + "%2F" + monthString + "%2F" + yearString
    return dateString


# Get the start date of the judgement to scrape
def getJudgementFromDate(bench, toDate, SOURCE):
    resultDate = dbpersistence.getJudgementFromDate(bench, SOURCE, CURSOR)
    if not resultDate is None and not resultDate[0] is None:
        fromDate = resultDate[0].strftime('%d-%m-%Y')
        from_dateObject = akmutility.formatdate_dmy(fromDate)
        judgementfromDate = constructDate(from_dateObject)
    else:
        judgementfromDate = toDate
    return judgementfromDate

# Get the start date of the judgement to scrape
def getAllJudgements():
    sql = "SELECT ID, CASE_NO, PETITIONER_NAME, JUDGEMENT_DATE, BENCH_COURT, SOURCE FROM JUDGEMENT_MASTER_DATA"
    try:
        # Execute the SQL command
        CURSOR.execute(sql)
        # Fetch Record
        results = CURSOR.fetchall()
        for result in results:
            fileName = constructFileName(result[1], result[2], result[3].strftime('%d-%m-%Y'), result[4], 'NCLT')
            print(fileName)
            updatesql = 'UPDATE JUDGEMENT_MASTER_DATA SET FILE_NAME = "'+ fileName + '"  WHERE ID = ' + str(result[0])
            print(updatesql)
            try:
                # Execute the SQL command
                CURSOR.execute(updatesql)
                MY_DB.commit()
            except:
                # Rollback in case there is any error
                logger.error('Error in Method - updatejudgementfilestatus --> ' + sql)
                MY_DB.rollback()
    except:
        print("Exception occured")
        logger.error(traceback.print_exc(file=sys.stdout))




def start(SOURCE, benchCourtList, fromDate):
    toDate = constructDate(date.today())
    for bench in benchCourtList:
        logger.info('Scrapping -----> ' + bench  )
        fromDate = getJudgementFromDate(bench, toDate, SOURCE)
        logger.info(akmutility.getStringWithThis("*"))
        logger.info(f"Looking for Judgements for {bench} from {fromDate} to {toDate}")
        courtId = parser.get('bench', bench)
        MAIN_URL_PATH = "https://nclt.gov.in/judgement-date-wise?field_bench_target_id=" + courtId + "&field_search_date_value%5Bmin%5D%5Bdate%5D="+ fromDate +"&field_search_date_value%5Bmax%5D%5Bdate%5D=" + toDate + "&page="
        # Get SOUP
        SOUP = getsoup(0, MAIN_URL_PATH, flag=True)
        no_rows = len(SOUP.find_all("tr")) - 1
        if no_rows <= 0:
            logger.error(MAIN_URL_PATH + ' - Data Not Available at the moment. Try again after sometime!')
            continue
        # Get Last Page
        LAST_PAGE = getlastpage(SOUP)
        # Get Last Updated Record if any - To load the delta records
        resultSet = dbpersistence.getlastupdatedjudgementrecord(bench, SOURCE, CURSOR)
        result = str(resultSet)
        resultstr = result[2:(len(result) - 3)]
        #resultstr = str(result).replace(",", "").replace("'", "").replace("(", "").replace(")", "")
        # print(result)
        updateflag = False
        dbupdate = False
        if not resultSet is None:
            logger.info("Latest records will be updated.")
            logger.info("Updating........................")
            logger.info("Last Updated Record Details - " + resultstr)
            # LAST_PAGE INSTEAD OF DELTA PAGE AS IT HAS TO TRAVERSE BETWEEN THE TWO DATE RANGES
            for i in range(LAST_PAGE, -1, -1):
                logger.info("Scanning page......")
                SOUP = getsoup(i, MAIN_URL_PATH, flag=True)
                # Get all data associated with this class
                no_rows = len(SOUP.find_all("tr")) - 1
                if no_rows <= 0:
                    logger.error(MAIN_URL_PATH + ' - Data Not Available at the moment. Try again after sometime!')
                    break
                # sys.exit()
                for row in SOUP.find_all("tr")[no_rows:0:-1]:
                    # Get all cells inside the row
                    basic_data_cells = row.findAll("td")
                    if not checkIBCCases(basic_data_cells):
                        continue
                    if updateflag:
                        dbInsert(basic_data_cells, bench, SOURCE)
                        dbupdate = True
                    else:
                        # print("update = false")
                        # print(getkeyvalues(basic_data_cells))
                        if resultstr == getkeyvalues(basic_data_cells):
                            # print("Result same as key values "+ getkeyvalues(basic_data_cells))
                            updateflag = True
                            continue
                        else:
                            continue
        else:
            for i in range(LAST_PAGE, -1, -1):
                SOUP = getsoup(i, MAIN_URL_PATH, flag=True)
                # Get all data associated with this class
                no_rows = len(SOUP.find_all("tr")) - 1
                # sys.exit()
                for row in SOUP.find_all("tr")[no_rows:0:-1]:
                    # Get all cells inside the row
                    basic_data_cells = row.findAll("td")
                    if not checkIBCCases(basic_data_cells):
                        continue
                    dbInsert(basic_data_cells, bench, SOURCE)

        if not dbupdate:
            logger.info(SOURCE + " Database is upto-date! ")

        logger.info(f"Judgements Scrapping for {bench} from {fromDate} to {toDate} - Completed!!")

    MY_DB.close()
    CURSOR.close()

# Main Entry
if __name__ == "__main__":
    from_dateObject = akmutility.formatdate_dmy(JUDGEMENT_FROM_DATE)
    fromDate = constructDate(from_dateObject)
    benchCourtList = akmutility.getBenchList()
    judicialBodiesList = akmutility.getJudicialBodiesList()
    logger.info(akmutility.getStringWithThis("-"))
    for SOURCE in judicialBodiesList:
        logger.info("JUDGEMENTS SCRAPPING FROM - " + SOURCE + " STARTED")
        start(SOURCE, benchCourtList, fromDate)
        logger.info("JUDGEMENTS SCRAPPING FROM - " + SOURCE + " COMPLETED")
        logger.info(akmutility.getStringWithThis("-"))





