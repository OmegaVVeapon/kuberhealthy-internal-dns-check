import sys
import os
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

#  config.load_incluster_config()
config.load_kube_config()

v1 = client.CoreV1Api()

def get_all_services(annotation=None, _continue=None, limit=None):
    try:
        return v1.list_service_for_all_namespaces(
                limit=limit,
                _continue=_continue,
                watch=False)
    except ApiException:
        logger.exception("Exception when calling CoreV1Api->list_service_for_all_namespaces")

def get_namespaced_service(namespace, label=None, field=None):
    try:
        return v1.list_namespaced_service(
                namespace=namespace,
                label_selector=label,
                field_selector=field,
                watch=False)
    except ApiException:
        logger.exception("Exception when calling CoreV1Api->list_namespaced_service")

def get_namespaced_endpoints(namespace, field):
    try:
        return v1.list_namespaced_endpoints(
                namespace=namespace,
                field_selector=field,
                watch=False)
    except ApiException:
        logger.exception("Exception when calling CoreV1Api->list_namespaced_endpoints")

def get_namespaced_pods(namespace, label):
    try:
        return v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label,
                watch=False)
    except ApiException:
        logger.exception("Exception when calling CoreV1Api->list_namespaced_pods")
