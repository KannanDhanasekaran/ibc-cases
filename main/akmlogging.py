import logging
import logging.handlers as handlers
from configparser import ConfigParser

# Parser for property file
parser = ConfigParser()
parser.read('..//config//akm.config')

# Log Location
APPLICATION_LOG_LOC = parser.get('log' , 'application_log_location')
ERROR_LOG_LOC = parser.get('log' , 'error_log_location')

# Get Logging configuration
# Create two logging files - Application & Error Log on a daily basis
def getLoggerconfig():
    logger = logging.getLogger('akm_log')
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Here we define our formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        logHandler = handlers.TimedRotatingFileHandler(APPLICATION_LOG_LOC, when='D', interval=1, backupCount=0)
        logHandler.setLevel(logging.INFO)
        logHandler.setFormatter(formatter)

        # errorLogHandler = handlers.RotatingFileHandler('error.log', maxBytes=5000, backupCount=0)
        errorLogHandler = handlers.TimedRotatingFileHandler(ERROR_LOG_LOC, when='D', interval=1, backupCount=0)
        errorLogHandler.setLevel(logging.ERROR)
        errorLogHandler.setFormatter(formatter)

        logger.addHandler(logHandler)
        logger.addHandler(errorLogHandler)
    return logger