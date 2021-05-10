# kuberhealthy-internal-dns-check

## What is this?

This is a Python-based `khc`(KuberhealthyCheck) for the [Kuberhealthy](https://github.com/Comcast/kuberhealthy) synthetic monitoring operation.

## How does it work?

It will query a Kubernetes cluster for certain annotated services.

Once such a service is found, it will be resolved against all the existing DNS pods in the the cluster.

If all nameservers resolve the service correctly, it will move on to find the next annotated service. 

Otherwise, a failure will be reported back to the Kuberhealthy master and the `khc` will exit non-zero.

## Why?

While there are existing [internal/external DNS KuberhealthyChecks](https://github.com/Comcast/kuberhealthy/blob/master/cmd/dns-resolution-check/README.md#dns-status-check) upstream, they didn't meet our needs for the
following reasons:

* Services aren't checked for IP consistency between what the nameservers resolve them to and what the IPs they actually map to. 
* Only one service can be checked per `khc`. However, for our purposes, we opted to change the model to be pulled-based via an annotation to simplify adoption across our many teams.

## Quickstart

First, create the necessary [RBAC permissions](rbac.yaml) necessary for the `khc`.

Then, apply the `khc` in [internal-dns-khc.yaml](examples/internal-dns-khc.yaml).

That's it.

Pods should begin spawning and any service in the cluster that contains the defined `ANNOTATION` will be checked.


## Dockerhub

All tags are automatically built and pushed to [Dockerhub](https://hub.docker.com/r/omegavveapon/kuberhealthy-internal-dns-check).

## Configuration Environment Variables

| Variable | Required? | Default | Description |
| --- |:---:|:---:| --- |
| ANNOTATION | <b>Yes</b> | `None` | Annotation that will need to be present in services for the check to pick them up |
| DNS_NAMESPACE | <b>Yes</b> | `None` | Namespace where the DNS pods are located |
| DNS_NODE_SELECTOR | <b>Yes</b> | `None` | The label belonging to the DNS pods |

## DNS pod selection

If you're confused about what your `DNS_NAMESPACE` and `DNS_NODE_SELECTOR` should be, simply test the following `kubectl` command:

```
kubectl get pods -o wide --namespace=<DNS_NAMESPACE> -l <DNS_NODE_SELECTOR>
```
