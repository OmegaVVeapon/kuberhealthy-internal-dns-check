import logging
from kh_status import kh_fail
from kube_helpers import get_all_services, get_namespaced_endpoints
from dns_helpers import get_ips_record

# TODO: Make log level configurable from env var
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_headless_endpoint_ips(headless_svc, namespace):
    logger.info("Getting the endpoint IPs for headless service: '%s'", headless_svc)

    headless_svc_eps = get_namespaced_endpoints(namespace, f"metadata.name={headless_svc}")

    headless_eps_ips = []
    for subset in headless_svc_eps.items[0].subsets:
        for address in subset.addresses:
            headless_eps_ips.append(address.ip)

    return sorted(headless_eps_ips)

def get_services_with_annotation(annotation=None, _continue=None, limit=None):
    services = get_all_services(_continue=_continue, limit=limit)

    filtered = {
        'services': [],
        'continue': services.metadata._continue,
        'remaining': services.metadata.remaining_item_count
    }

    for item in services.items:
        if item.metadata.annotations is not None and annotation in item.metadata.annotations:
            filtered['services'].append({
                'name': item.metadata.name,
                'namespace': item.metadata.namespace,
                'cluster_ip': item.spec.cluster_ip
            })

    return filtered

def resolve_service(service, namespace, cluster_ip, nameservers):

    qualified_service = f"{service}.{namespace}"

    if cluster_ip:
        comparison_ips = [cluster_ip]
    else:
        comparison_ips = get_headless_endpoint_ips(service, namespace)

    for nameserver in nameservers:
        ips_record = get_ips_record(qualified_service, [nameserver])
        ips_record_answer = sorted(ips_record.answer)

        if set(ips_record_answer).difference(comparison_ips):
            kh_fail(f"Nameserver: '{nameserver}' resolved IP '{ips_record_answer}' when the expected IP was '{cluster_ip}'")

        logger.info("All nameservers resolved '%s' correctly!", qualified_service)
