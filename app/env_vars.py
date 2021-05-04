import os
import logging
from kh_status import kh_fail

# TODO: Make log level configurable from env var
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_required_env_var(name):
    """Returns value of a required environment variable. Fails if not found"""
    try:
        return os.environ[name]
    except KeyError:
        kh_fail(f"{name} environment variable is required!")

def get_env_var_bool(name):
    """Gets value of environment variable as a boolean. If not 'true', returns False"""
    return os.getenv(name) == 'true'

def get_env_var_int(name, default):
    """Gets value of environment variable as an int. If not a valid int,
    returns the given default value"""
    env_var = os.getenv(name, default)
    try:
        return int(env_var)
    except TypeError:
        logger.warning("Expected integer value for %s and got %s. Returning %s instead", name, env_var, default)
        return default
