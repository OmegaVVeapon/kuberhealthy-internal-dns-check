import os
import logging
from dns_helpers import *
from env_vars import get_env_var_int, get_required_env_var
from services import get_services_with_annotation, resolve_service
from kh_status import kh_fail, kh_success
from pprint import pprint

# TODO: Make log level configurable from env var
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ANNOTATION = get_required_env_var('ANNOTATION')
DNS_NODE_SELECTOR = get_required_env_var('DNS_NODE_SELECTOR')
DNS_NAMESPACE = get_required_env_var('DNS_NAMESPACE')

logger.info("ANNOTATION env var provided as: '%s'", ANNOTATION)
logger.info("DNS_NODE_SELECTOR env var provided as: '%s'", DNS_NODE_SELECTOR)
logger.info("DNS_NAMESPACE env var provided as: '%s'", DNS_NAMESPACE)

# Get the max number of services we will check for pagination
MAX_SERVICES = get_env_var_int('MAX_SERVICES', 30)

# Verify that the Kubernetes master Service works. If it doesn't, then there's
# no need to check anything else, we have bigger problems.
# https://kubernetes.io/docs/tasks/debug-application-cluster/debug-service/#does-any-service-exist-in-dns
logger.info("Attempting to resolve the kubernetes master service")
ips_record = get_ips_record("kubernetes.default")
logger.info("Service: 'kubernetes.default' resolved successfully")

### DNS section ###

dns_svc = get_dns_svc(DNS_NAMESPACE, DNS_NODE_SELECTOR)

dns_svc_name = dns_svc.metadata.name
dns_svc_ip = dns_svc.spec.cluster_ip

logger.info("Successfully found DNS service: '%s' with IP: '%s'",
        dns_svc_name,
        dns_svc_ip)

dns_eps_ips = get_dns_endpoint_ips(DNS_NAMESPACE, dns_svc_name)
dns_pod_ips = get_dns_pod_ips(DNS_NAMESPACE, DNS_NODE_SELECTOR)

logger.info("Found DNS endpoint IPs: %s", dns_eps_ips)
logger.info("Found DNS pod IPs: %s", dns_pod_ips)

if set(dns_eps_ips).difference(dns_pod_ips):
    kh_fail("DNS service has mismatching endpoints and pod IPs!")
else:
    logger.info("Successfully matched DNS endpoint and pod IPs.")

### SVC LOOKUP SECTION ###

logger.info("Looking for services with annotation '%s'", ANNOTATION)
_continue = None

# Search through all the services in the cluster for annotated ones
while True:
    annotated_services = get_services_with_annotation(
            annotation=ANNOTATION,
            _continue=_continue,
            limit=MAX_SERVICES
            )

    if annotated_services['services']:
        #  pprint(annotated_services['services'])
        for service in annotated_services['services']:
            resolve_service(
                service=service['name'],
                namespace=service['namespace'],
                cluster_ip=service['cluster_ip'],
                nameservers=dns_pod_ips
            )

    _continue = annotated_services['continue']

    if not annotated_services['continue']:
        break

    logger.debug("%s services remaining to check", annotated_services['remaining'])
