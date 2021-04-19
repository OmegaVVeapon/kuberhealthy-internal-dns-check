import os
import sys
import logging
from kh_client import *
from dns_helpers import *
from headless import get_headless_endpoint_ips
from pprint import pprint

# TODO: Make log level configurable from env var
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    HOSTNAME = os.environ['HOSTNAME']
except KeyError as e:
    logger.error("HOSTNAME environment variable is required!")
    sys.exit(1)

logger.info("HOSTNAME env var provided as: '%s'", HOSTNAME)

DNS_NODE_SELECTOR = os.getenv('DNS_NODE_SELECTOR')
NAMESPACE = os.getenv('NAMESPACE')

if NAMESPACE:
    logger.info("NAMESPACE env var provided as: '%s'", NAMESPACE)

if DNS_NODE_SELECTOR:
    logger.info("DNS_NODE_SELECTOR env var provided as: '%s'", DNS_NODE_SELECTOR)

if None not in (NAMESPACE, DNS_NODE_SELECTOR):
    logger.info("NAMESPACE and DNS_NODE_SELECTOR have both been provided. DNS endpoint checking is enabled.")

    dns_svc = get_dns_svc(NAMESPACE, DNS_NODE_SELECTOR)

    dns_svc_name = dns_svc.metadata.name
    dns_svc_ip = dns_svc.spec.cluster_ip

    logger.info("Successfully found DNS service: '%s' with IP: '%s'",
            dns_svc_name,
            dns_svc_ip)

    dns_eps_ips = get_dns_endpoint_ips(NAMESPACE, dns_svc_name)
    dns_pod_ips = get_dns_pod_ips(NAMESPACE, DNS_NODE_SELECTOR)

    logger.info("Found DNS endpoint IPs: %s", dns_eps_ips)
    logger.info("Found DNS pod IPs: %s", dns_pod_ips)

    if not dns_eps_ips or not dns_pod_ips:
        logger.error("Both the DNS endpoints and pod ips should have been found!")
        sys.exit(1)

    if set(dns_eps_ips).difference(dns_pod_ips):
        logger.error("DNS service has mismatching endpoints and pod IPs!")
        sys.exit(1)
    else:
        logger.info("Successfully matched DNS endpoint and pod IPs.")
else:
    logger.info("NAMESPACE is '%s' and DNS_NODE_SELECTOR is '%s'. They both need to be provided for DNS endpoint checks. Skipping", NAMESPACE, DNS_NODE_SELECTOR)

# Verify that the Kubernetes master Service works. If it doesn't, then there's
# no need to check anything else, we have bigger problems.
# https://kubernetes.io/docs/tasks/debug-application-cluster/debug-service/#does-any-service-exist-in-dns

logger.info("Attempting to resolve the kubernetes master service")
ips_record = get_ips_record("kubernetes.default", [dns_svc_ip])

if not ips_record.answer:
    logger.error("Could not resolve master service: kubernetes.default")
    #  exit(1)

logger.info("Service: 'kubernetes.default' resolved successfully")

# Check if the HOSTNAME is qualified, if so, extract the hostname and namespace.

hostname_list = HOSTNAME.split('.')

if len(hostname_list) > 1:
    hostname = hostname_list[0]
    hostname_namespace = hostname_list[1]
    logger.info("HOSTNAME: '%s' seems to be qualified. Assuming namespace: '%s'", HOSTNAME, hostname_namespace)
else:
    hostname = HOSTNAME
    hostname_namespace = 'default'
    logger.info("Non-qualified HOSTNAME: '%s' was given. Assuming namespace: '%s'", HOSTNAME, hostname_namespace)

logger.info("Looking for HOSTNAME: '%s' in namespace: '%s'", hostname, hostname_namespace)

hostname_svc = get_namespaced_service(hostname_namespace, field=f"metadata.name={hostname}")

if not hostname_svc.items:
    logger.error("Could not find '%s'. Check that it exists in the '%s' namespace.", hostname, hostname_namespace)
    sys.exit(1)

hostname_svc_ip = hostname_svc.items[0].spec.cluster_ip
logger.info("Found '%s' with IP: '%s'", HOSTNAME, hostname_svc_ip)

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
            logger.error("Nameserver: '%s' resolved IP '%s' when the expected IP was '%s'", nameserver, ips_record_answer, comparison_ips)
            sys.exit(1)
    logger.info("All nameservers resolved '%s' correctly!", HOSTNAME)

#  fail = os.getenv("FAIL", None)

#  if fail:
#      print("Reporting failure.")
#      try:
#          report_failure(["example failure message"])
#      except Exception as e:
#          print(f"Error when reporting failure: {e}")
#          exit(1)
#  else:
#      print("Reporting success.")
#      try:
#          report_success()
#      except Exception as e:
#          print(f"Error when reporting success: {e}")
#          exit(1)
#  exit(0)
