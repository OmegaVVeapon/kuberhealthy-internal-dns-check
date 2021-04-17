import os
import sys
import logging
from kh_client import *
from dns_helpers import *

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

    dns_eps_ips = get_dns_endpoint_ips(NAMESPACE, DNS_NODE_SELECTOR)
    dns_pod_ips = get_dns_pod_ips(NAMESPACE, DNS_NODE_SELECTOR)

    logger.info("Found DNS endpoint IPs: %s", dns_eps_ips)
    logger.info("Found DNS pod IPs: %s", dns_pod_ips)

    if not dns_eps_ips or not dns_pod_ips:
        logger.error("Both the DNS endpoints and pod ips should have been found!") 

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

#  ips_record = get_ips_record("kubernetes.default")

#  if not ips_record.answer:
#      exit(1)

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

logger.info("Looking for service name: '%s' in namespace: '%s'", hostname, hostname_namespace)

hostname_svc = get_namespaced_service(hostname_namespace, field=f"metadata.name={hostname}")

if not hostname_svc.items:
    logger.error("Could not find service '%s' in namespace '%s'. Check that it exists in that namespace.", hostname, hostname_namespace)
    sys.exit(1)

pprint(hostname_svc.items[0].spec.cluster_ip)

#  if dns_svc.items[0].metadata.name != 'kube-dns':
#      sys.exit(1)

#  ret = v1.list_pod_for_all_namespaces(watch=False)
#  for i in ret.items:
#      print("%s\t%s\t%s" %
#            (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


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
