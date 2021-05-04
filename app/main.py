import os
import logging
from dns_helpers import *
from env_vars import get_env_var_int, get_required_env_var
from services import get_services_with_annotation
from headless import get_headless_endpoint_ips
from kh_status import kh_fail, kh_success
import sys
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

logger.info("Looking for services with annotation '%s'", ANNOTATION)
_continue = None
while True:
    annotated_services = get_services_with_annotation(
            annotation='please-check',
            _continue=_continue,
            limit=MAX_SERVICES
            )

    if annotated_services['services']:
        pprint(annotated_services['services'])

    _continue = annotated_services['continue']

    if not annotated_services['continue']:
        break

    logger.debug("%s services remaining to check", annotated_services['remaining'])

##### DNS section

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

sys.exit(0)

# Verify that the Kubernetes master Service works. If it doesn't, then there's
# no need to check anything else, we have bigger problems.
# https://kubernetes.io/docs/tasks/debug-application-cluster/debug-service/#does-any-service-exist-in-dns

logger.info("Attempting to resolve the kubernetes master service")

# If we got the information to find the DNS service's IP use it explicitely as the nameserver
# Otherwise, let the default nameserver be used
if dns_svc_ip:
    ips_record = get_ips_record("kubernetes.default", [dns_svc_ip])
else:
    ips_record = get_ips_record("kubernetes.default")

logger.info("Service: 'kubernetes.default' resolved successfully")

# Check if the HOSTNAME is qualified, if so, extract the hostname and namespace.

hostname_list = HOSTNAME.split('.')

if len(hostname_list) > 1:
    hostname = hostname_list[0]
    hostname_namespace = hostname_list[1]
    logger.info("HOSTNAME: '%s' seems to be qualified. Inferring namespace: '%s'", HOSTNAME, hostname_namespace)
else:
    hostname = HOSTNAME
    hostname_namespace = 'default'
    logger.info("Non-qualified HOSTNAME: '%s' was given. Assuming namespace: '%s'", HOSTNAME, hostname_namespace)

logger.info("Looking for HOSTNAME: '%s' in namespace: '%s'", hostname, hostname_namespace)

hostname_svc = get_namespaced_service(hostname_namespace, field=f"metadata.name={hostname}")

if not hostname_svc.items:
    kh_fail(f"Could not find service '{hostname}'. Check that it exists in the '{hostname_namespace}' namespace")

hostname_svc_ip = hostname_svc.items[0].spec.cluster_ip
logger.info("Found service '%s' with ClusterIP: '%s'", HOSTNAME, hostname_svc_ip)

#TODO: I feel like this could be refactored to be made simpler... need to come back to this later

# If we were able to obtain the nameserver IPs, verify they are working correctly
if dns_eps_ips:
    # If we're dealing with a headless svc, get the endpoint IP list and use it to compare against the resolved IPs
    # Otherwise, just use the normal non-headless clusterIP that we obtained previously
    if hostname_svc_ip == 'None':
        comparison_ips = get_headless_endpoint_ips(hostname_namespace, hostname)
        logger.info("Found endpoint IPs %s for headless service '%s'", comparison_ips, HOSTNAME)
    else:
        comparison_ips = [hostname_svc_ip]

    logger.info("Attempting to resolve '%s' with all DNS nameservers previously found", HOSTNAME)
    for nameserver in dns_eps_ips:
        ips_record = get_ips_record(HOSTNAME, [nameserver])
        ips_record_answer = sorted(ips_record.answer)
        logger.info("Nameserver '%s' resolved hostname to %s", nameserver, ips_record_answer)
        if set(ips_record_answer).difference(comparison_ips):
            kh_fail(f"Nameserver: '{nameserver}' resolved IP '{ips_record_answer}' when the expected IP was '{comparison_ips}'")
    logger.info("All nameservers resolved '%s' correctly!", HOSTNAME)
else:
    # If we didn't have the info to find the DNS servers and we were provided a non-headless service, at least try to resolve it with the default nameserver
    # There's nothing we can do about non-headless services...
    if hostname_svc_ip != 'None':
        ips_record = get_ips_record(HOSTNAME)

        ips_record_answer = sorted(ips_record.answer)
        comparison_ip = [hostname_svc_ip]

        if set(ips_record_answer).difference(comparison_ip):
            kh_fail(f"Default nameserver resolved IP '{ips_record_answer}' when the expected IP was '{comparison_ip}'")
        else:
            logger.info("Default nameserver resolved '%s' to %s which is correct!", HOSTNAME, ips_record_answer)

kh_success()
