import sys
import logging
from kube_helpers import *
from nslookup import Nslookup

# TODO: Make log level configurable from env var
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_dns_endpoint_ips(namespace, dns_node_selector):
    logger.info("Looking for DNS service with label: '%s'", dns_node_selector)

    dns_svc = get_namespaced_service(namespace, dns_node_selector)

    if not dns_svc.items:
        logger.error("Could not find DNS service")
        sys.exit(1)

    DNS_SVC_NAME = dns_svc.items[0].metadata.name

    logger.info("Successfully found %s DNS service with IP %s",
            DNS_SVC_NAME,
            dns_svc.items[0].spec.cluster_ip)

    logger.info("Getting the endpoint IPs for DNS service: '%s'", DNS_SVC_NAME)

    dns_eps = get_namespaced_endpoints(namespace, 'metadata.name=kube-dns')

    dns_eps_ips = []
    for subset in dns_eps.items[0].subsets:
        for address in subset.addresses:
            dns_eps_ips.append(address.ip)

    return sorted(dns_eps_ips)

def get_dns_pod_ips(namespace, dns_node_selector):
    logger.info("Looking for the DNS pods with label: '%s' in the '%s' namespace", dns_node_selector, namespace)

    dns_pods = get_namespaced_pods(namespace, dns_node_selector)

    dns_pod_ips = []
    for i in dns_pods.items:
        dns_pod_ips.append(i.status.pod_ip)

    return sorted(dns_pod_ips)

def get_ips_record(hostname, dns_servers=[]):
    dns_query = Nslookup(dns_servers)
    logger.info("Resolving hostname: '%s' with dns_servers: %s", hostname, dns_servers)
    return dns_query.dns_lookup(hostname)
