#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Sun Nov 17 23:20:33 2019

@author: Kannan
"""

import time
import sys
from configparser import ConfigParser
import akmlogging
import dbpersistence
import requests  # library to load html data from url
from bs4 import BeautifulSoup  # library for webscraping

import akmutility
import dbconfiguration

# Get Logger
from urllib3.exceptions import ReadTimeoutError

logger = akmlogging.getLoggerconfig()

# Parser for property file
parser = ConfigParser()
parser.read('..//config//akm.config')

# Get DB connection
MY_DB = dbconfiguration.getDB()
#logger.info('Establishing Database Connection.. ' + str(MY_DB))

# Prepare a cursor object using cursor() method
CURSOR = MY_DB.cursor()

# Source - From where this data is being scrapped
# SOURCE = parser.get('source', 'source_cirp')

# Page to traverse from - To load delta value
DELTA_PAGE = int(parser.get('update', 'delta_from_page'))

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
            if flag == True:
                logger.info("Scraping URL ---->" + URL_TO_SCRAPE)
            # Load html's plain data into a variable
            PLAIN_HTML_TEXT = requests.get(URL_TO_SCRAPE)

            # parse the data
            SOUP = BeautifulSoup(PLAIN_HTML_TEXT.text, "html.parser")
            is_done = True
        except ReadTimeoutError:
            retry += 1
            time.sleep(sleep_interval)
    if not is_done:
        logger.error(URL_TO_SCRAPE +' - could not be loaded')
    return SOUP


# Last Page Function
def getlastpage(SOUP, SOURCE):
    LAST_PAGE_URL = SOUP.find("li", {"last"})
    #print(LAST_PAGE_URL)
    LP_HREF = LAST_PAGE_URL.find('a').get('href')
    #print(LP_HREF)
    if akmutility.ispublicannounecment(SOURCE):
        PAGE_INDEX = LP_HREF.find("&page=")
    else:
        PAGE_INDEX = LP_HREF.find("?page=")
    #print(PAGE_INDEX)
    LAST_PAGE = int(LP_HREF[PAGE_INDEX + 6:])
    #print(LAST_PAGE)
    return LAST_PAGE


# Get Field values
def getfieldvalues_pa(basic_data_cells):
    date_announcement = basic_data_cells[0].text.strip()
    date_announcement_obj = akmutility.formatdate_dmy(date_announcement)
    last_date_submission = basic_data_cells[1].text.strip()
    if len(last_date_submission) > 0:
        last_date_submission_obj = akmutility.formatdate_dmy(last_date_submission)
    else:
        last_date_submission_obj = ''
    corp_debtor_name = basic_data_cells[2].text.strip()
    corp_debtor_name = akmutility.format_single_quote(corp_debtor_name)
    applicant_name = basic_data_cells[3].text.strip()
    applicant_name = akmutility.format_single_quote(applicant_name)
    name_ip = basic_data_cells[4].text.strip()
    name_ip = akmutility.format_single_quote(name_ip)
    address_ip = basic_data_cells[5].text.strip()
    address_ip = akmutility.format_single_quote(address_ip)
    address_ip = address_ip.replace('"','')
    pa_url = basic_data_cells[6].find('a').get('onclick')
    start = pa_url.find('https')
    end = pa_url.find('.pdf')
    pa_pdf_link = pa_url[start:end + 4]
    remarks = basic_data_cells[7].text.strip()
    remarks = akmutility.format_single_quote(remarks)
    return date_announcement_obj, last_date_submission_obj, corp_debtor_name, applicant_name, name_ip, address_ip, pa_pdf_link, remarks


# Get Field values
def getfieldvalues_irp(basic_data_cells):
    corp_debtor_name = basic_data_cells[0].text.strip()
    corp_debtor_name = akmutility.format_single_quote(corp_debtor_name)
    rp_name = basic_data_cells[1].text.strip()
    rp_name = akmutility.format_single_quote(rp_name)
    date_inv_rplan = basic_data_cells[2].text.strip()
    date_inv_rplan_obj = akmutility.formatdate_dmonthyear(date_inv_rplan)
    date_iss_em = basic_data_cells[3].text.strip()
    date_iss_em_obj = akmutility.formatdate_dmonthyear(date_iss_em)
    last_date_submission_rplan = basic_data_cells[4].text.strip()
    last_date_submission_rplan_obj = akmutility.formatdate_dmonthyear(last_date_submission_rplan)
    pa_url = basic_data_cells[5].find('a').get('onclick')
    start = pa_url.find('https')
    end = pa_url.find('.pdf')
    pa_pdf_link = pa_url[start:end + 4]
    remarks = basic_data_cells[6].text.strip()
    remarks = akmutility.format_single_quote(remarks)
    return corp_debtor_name, rp_name, date_inv_rplan_obj, date_iss_em_obj, last_date_submission_rplan_obj, pa_pdf_link, remarks


# Get Key Values Function - @Return - (Date of Announcement + Last Date of Submission + Corp Debtor Name)
def getkeyvalues(basic_data_cells, SOURCE):
    if akmutility.ispublicannounecment(SOURCE):
        date_announcement = basic_data_cells[0].text.strip()
        date_announcement_obj = akmutility.formatdate_dmy(date_announcement)
        last_date_submission = basic_data_cells[1].text.strip()
        if len(last_date_submission) > 0:
            last_date_submission_obj = akmutility.formatdate_dmy(last_date_submission)
        else:
            last_date_submission_obj = ''
        corp_debtor_name = basic_data_cells[2].text.strip()
        corp_debtor_name = akmutility.format_single_quote(corp_debtor_name)
        return str(date_announcement_obj) + str(last_date_submission_obj) + corp_debtor_name
    else:
        corp_debtor_name = basic_data_cells[0].text.strip()
        corp_debtor_name = akmutility.format_single_quote(corp_debtor_name)
        rp_name = basic_data_cells[1].text.strip()
        rp_name = akmutility.format_single_quote(rp_name)
        date_inv_rplan = basic_data_cells[2].text.strip()
        date_inv_rplan_obj = akmutility.formatdate_dmonthyear(date_inv_rplan)
        return corp_debtor_name + rp_name + str(date_inv_rplan_obj)


#pa_fetch_links = SELECT ID, CONCAT(SUBSTRING(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(CORP_DEBTOR_NAME, ' ', ''), '.',''),'-',''), ',',''), '&',''),'/',''),1,10),SUBSTRING(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(APPLICANT_NAME, ' ', ''), '.',''),'-',''), ',',''), '&',''),'/',''),1,10), REPLACE(DATE_ANNOUNCEMENT,'-','')) AS FILE_NAME, LINK FROM IBBI_WEB_MASTERDATA WHERE IS_FILE_DOWNLOADED = 'N' AND IS_VALID_LINK IS NULL AND SOURCE =

# Construct File Name
def constructFileName(corp_debtor_name, applicant_or_ipname, dannouncement_or_dateresplan_obj, SOURCE):
    corp_debtor_name_temp = corp_debtor_name.replace(' ', '').replace('.', '').replace('-', '').replace(',',
                                                                                                        '').replace('&',
                                                                                                                    '').replace(
        '/', '').replace('(', '').replace(')', '').replace('"', '').replace("'", '')
    if len(corp_debtor_name_temp) >= 10:
        corp_debtor_name_temp_ = corp_debtor_name_temp[:10]
    else:
        corp_debtor_name_temp_ = corp_debtor_name_temp
    applicant_name_or_ip_name_temp = applicant_or_ipname.replace(' ', '').replace('.', '').replace('-', '').replace(',', '').replace(
        '&', '').replace('/', '').replace('(', '').replace(')', '').replace('"', '').replace("'", '')
    if len(applicant_name_or_ip_name_temp) >= 10:
        applicant_name_or_ip_name_temp_ = applicant_name_or_ip_name_temp[:10]
    else:
        applicant_name_or_ip_name_temp_ = applicant_name_or_ip_name_temp
    date_announcement_or_ldaterp_temp = str(dannouncement_or_dateresplan_obj).replace('-', '')
    fileName = corp_debtor_name_temp_ + applicant_name_or_ip_name_temp_ + date_announcement_or_ldaterp_temp
    #print(fileName)
    if akmutility.ispublicannounecment(SOURCE):
        results = dbpersistence.checkIfPARecordAlreadyExists(corp_debtor_name, applicant_or_ipname, dannouncement_or_dateresplan_obj,
                                                         SOURCE, CURSOR)
    else:
        results = dbpersistence.checkIfIRPRecordAlreadyExists(corp_debtor_name, applicant_or_ipname,
                                                             dannouncement_or_dateresplan_obj,
                                                             SOURCE, CURSOR)
    if len(results) == 0:
        fileName = fileName + PDF_EXTN
        resultsFile = dbpersistence.checkifFileExists(fileName, SOURCE, CURSOR)
        if len(resultsFile) > 0:
            corp_debtor_name_temp_ = corp_debtor_name_temp[:18]
            applicant_name_or_ip_name_temp_ = applicant_name_or_ip_name_temp[:18]
            fileName = corp_debtor_name_temp_ + applicant_name_or_ip_name_temp_ + date_announcement_or_ldaterp_temp
            fileName = fileName + PDF_EXTN
            #print(fileName)
        return fileName
    else:
        duplicateIndex = []
        #print(results)
        for result in results:
            file_Name = result[0].replace(PDF_EXTN, '')
            #print(fileName)
            index = file_Name.find(DUPLICATE_LABEL)
            #print(index)
            if index == -1:
                duplicateIndex.append(0)
            else:
                indexfound = (int)(file_Name[index + 2:])
                duplicateIndex.append(indexfound)
            #print(duplicateIndex)
        maxValue = max(duplicateIndex) + 1
        fileName = fileName + DUPLICATE_LABEL + str(maxValue) + PDF_EXTN
    return fileName


def dbInsert(basic_data_cells, SOURCE):
    if akmutility.ispublicannounecment(SOURCE):
        last_date_submission = basic_data_cells[1].text.strip()
        # get all the different data from the table's tds
        [date_announcement_obj, last_date_submission_obj, corp_debtor_name, applicant_name, name_ip, address_ip,
         pa_pdf_link, remarks] = getfieldvalues_pa(basic_data_cells)
        fileName = constructFileName(corp_debtor_name,applicant_name,date_announcement_obj, SOURCE)
        #print(fileName)
        # save into database
        dbpersistence.insert_pa_db(date_announcement_obj, last_date_submission, last_date_submission_obj,
                                   corp_debtor_name,
                                   applicant_name, name_ip, address_ip, pa_pdf_link, fileName, SOURCE, remarks, MY_DB,
                                   CURSOR)
    else:
        # get all the different data from the table's tds
        [corp_debtor_name, rp_name, date_inv_rplan_obj, date_iss_em_obj, last_date_submission_rplan_obj, pa_pdf_link,
         remarks] = getfieldvalues_irp(basic_data_cells)
        fileName = constructFileName(corp_debtor_name, rp_name, date_inv_rplan_obj, SOURCE)
        # save into database
        dbpersistence.insert_irp_db(corp_debtor_name, rp_name, date_inv_rplan_obj, date_iss_em_obj,
                                   last_date_submission_rplan_obj, pa_pdf_link, fileName, SOURCE, remarks, MY_DB,
                                   CURSOR)

def dbInsert_v0(basic_data_cells, SOURCE):
    if akmutility.ispublicannounecment(SOURCE):
        last_date_submission = basic_data_cells[1].text.strip()
        # get all the different data from the table's tds
        [date_announcement_obj, last_date_submission_obj, corp_debtor_name, applicant_name, name_ip, address_ip,
         pa_pdf_link, remarks] = getfieldvalues_pa(basic_data_cells)

        # save into database
        dbpersistence.insert_pa_db(date_announcement_obj, last_date_submission, last_date_submission_obj,
                                   corp_debtor_name,
                                   applicant_name, name_ip, address_ip, pa_pdf_link, SOURCE, remarks, MY_DB,
                                   CURSOR)
    else:
        # get all the different data from the table's tds
        [corp_debtor_name, rp_name, date_inv_rplan_obj, date_iss_em_obj, last_date_submission_rplan_obj, pa_pdf_link,
         remarks] = getfieldvalues_irp(basic_data_cells)

        # save into database
        dbpersistence.insert_irp_db(corp_debtor_name, rp_name, date_inv_rplan_obj, date_iss_em_obj,
                                   last_date_submission_rplan_obj, pa_pdf_link, SOURCE, remarks, MY_DB,
                                   CURSOR)


def start(inputVar):
    START_TIME = time.time()
    #inputVar = str(
    #    input('Provide the source from where the information has to be scraped [PA_CIRP, PA_VLP, PA_LP, IRP] : '))
    #[SOURCE, MAIN_URL_PATH] = akmutility.checkinputargumentandgeturl(inputVar)
    #logger.info(
    #    "*********************************************************************************************************")
    #logger.info(f'IBBI WEB MASTER DATA scrapping - {inputVar} .....')

    [SOURCE, MAIN_URL_PATH] = akmutility.getURLforsource(inputVar)
    # print("Main Path "+MAIN_URL_PATH)
    # Get SOUP
    SOUP = getsoup(1, MAIN_URL_PATH, flag=False)

    # Get Last Page
    LAST_PAGE = getlastpage(SOUP, SOURCE)
    #print(LAST_PAGE)

    # LAST_PAGE = 1

    # Get Last Updated Record if any - To load the delta records
    result = dbpersistence.getlastupdatedrecord(SOURCE, CURSOR)
    #print(result)
    updateflag = False
    dbupdate = False
    if not result is None:
        logger.info("Latest records will be updated.")
        logger.info("Updating........................")
        resultstr = str(result).replace(",", "").replace("'", "").replace("(", "").replace(")", "")
        logger.info("Last Updated Record Details - " + resultstr)
        for i in range(DELTA_PAGE, 0, -1):
            logger.info("Scanning page......")
            SOUP = getsoup(i, MAIN_URL_PATH, flag=True)
            # Get all data associated with this class
            no_rows = len(SOUP.find_all("tr")) - 1
            # sys.exit()
            for row in SOUP.find_all("tr")[no_rows:0:-1]:
                # Get all cells inside the row
                basic_data_cells = row.findAll("td")
                if updateflag:
                    dbInsert(basic_data_cells, SOURCE)
                    dbupdate = True
                else:
                    # print("update = false")
                    # print(getkeyvalues(basic_data_cells))
                    if resultstr == getkeyvalues(basic_data_cells, SOURCE):
                        # print("Result same as key values "+ getkeyvalues(basic_data_cells))
                        updateflag = True
                        continue
                    else:
                        continue
    else:
        for i in range(LAST_PAGE, 0, -1):
            SOUP = getsoup(i, MAIN_URL_PATH, flag=True)
            # Get all data associated with this class
            no_rows = len(SOUP.find_all("tr")) - 1
            # sys.exit()
            for row in SOUP.find_all("tr")[no_rows:0:-1]:
                # Get all cells inside the row
                basic_data_cells = row.findAll("td")
                dbInsert(basic_data_cells, SOURCE)

    if not dbupdate:
        logger.info(SOURCE + " Database is upto-date! ")

    MY_DB.close()
    CURSOR.close()

    END_TIME = time.time()

    #logger.info("******************************************************************************************************************")
    logger.info(akmutility.getStringWithThis("*"))
    logger.info(f"Time taken to scrape the IBBI information from {inputVar} is {END_TIME - START_TIME} seconds ")
    logger.info(akmutility.getStringWithThis("*"))
    #logger.info("******************************************************************************************************************")

#Main Entry
if __name__ == "__main__":
    # print command line arguments
    for arg in sys.argv[1:]:
        start(arg)