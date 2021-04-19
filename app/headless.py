import sys
import logging
from kube_helpers import *

# TODO: Make log level configurable from env var
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_headless_endpoint_ips(namespace, headless_svc_name):
    logger.info("Getting the endpoint IPs for headless service: '%s'", headless_svc_name)

    headless_svc_eps = get_namespaced_endpoints(namespace, f"metadata.name={headless_svc_name}")

    headless_eps_ips = []
    for subset in headless_svc_eps.items[0].subsets:
        for address in subset.addresses:
            headless_eps_ips.append(address.ip)

    return sorted(headless_eps_ips)
