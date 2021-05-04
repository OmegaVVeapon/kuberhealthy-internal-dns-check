import logging
from kh_status import kh_fail
from kube_helpers import get_all_services

# TODO: Make log level configurable from env var
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

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
