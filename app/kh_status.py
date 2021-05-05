import sys
import logging
from kh_client import *

# TODO: Make log level configurable from env var
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def kh_fail(fail_message):
    logger.error(fail_message)
    logger.info("Reporting failure to Kuberhealthy master")
    try:
        report_failure([fail_message])
    except Exception as e:
        logger.error("Could not report failure: %s", e)
    sys.exit(1)

def kh_success():
    logger.info("Reporting success back to Kuberhealthy")
    try:
        report_success()
    except Exception as e:
        logger.error("Could not report success: %s", e)
        sys.exit(1)
