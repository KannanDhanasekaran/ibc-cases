# Test Scrapping module to test web scrapping of IBBI and download PDFs

import os
import time
from configparser import ConfigParser

import akmlogging
import akmutility

# print(sys.path)

# Get Logger
logger = akmlogging.getLoggerconfig()

# Parser for property file
parser = ConfigParser()
parser.read('..//config//akm.config')

START_TIME = time.time()
logger.info("@@@@@@@@@@@@@@@@@@@@@@  JUDGEMENTS SCRAPPING AND DOWNLOADING JOB - STARTED @@@@@@@@@@@@@@@@@@@@@@@@@@@")
os.system("python judgement_scraper_main.py")
os.system("python judgement_download_main.py")
logger.info("@@@@@@@@@@@@@@@@@@@@@@  JUDGEMENTS SCRAPPING AND DOWNLOADING JOB - COMPLETED @@@@@@@@@@@@@@@@@@@@@@@@@@@")
END_TIME = time.time()

logger.info(akmutility.getStringWithThis("^"))
logger.info(
    f"Total Time taken to scrape and download the Judgements / Update Database is {END_TIME - START_TIME} seconds ")
logger.info(akmutility.getStringWithThis("^"))
