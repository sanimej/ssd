#!/usr/bin/python

import sys, signal, time
import docker
import re
import subprocess
import json
import hashlib

ipv4match = re.compile(
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9]).' +
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9]).' +
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9]).' +
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])'
)


def get_namespaces(data, ingress=False):
    if ingress is True:
        return {"Ingress":"/var/run/docker/netns/ingress_sbox"}
    else:
        spaces =[]
        for c in data["Containers"]:
            sandboxes = {str(c) for c in data["Containers"]}

        containers = {}
        for s in sandboxes:
            spaces.append(str(cli.inspect_container(s)["NetworkSettings"]["SandboxKey"]))
            inspect = cli.inspect_container(s)
            containers[str(inspect["Name"])] = str(inspect["NetworkSettings"]["SandboxKey"])
        return containers


def check_network(nw_name, ingress=False):

    print "Verifying LB programming for containers on network %s" % nw_name

    data = cli.inspect_network(nw_name, verbose=True)

    services = data["Services"]
    fwmarks = {str(service): str(svalue["LocalLBIndex"]) for service, svalue in services.items()}

    stasks = {}
    for service, svalue in services.items():
        if service == "":
            continue
        tasks = []
        for task in svalue["Tasks"]:
            tasks.append(str(task["EndpointIP"]))
        stasks[fwmarks[str(service)]] = tasks

    containers = get_namespaces(data, ingress)
    for container, namespace in containers.items():
        print "Verifying container %s..." % container
        ipvs = subprocess.check_output(['/usr/bin/nsenter', '--net=%s' % namespace, '/usr/sbin/ipvsadm', '-ln'])

        mark = ""
        realmark = {}
        for line in ipvs.splitlines():
            if "FWM" in line:
                mark = re.findall("[0-9]+", line)[0]
                realmark[str(mark)] = []
            elif "->" in line:
                if mark == "":
                    continue
                ip = ipv4match.search(line)
                if ip is not None:
                    realmark[mark].append(format(ip.group(0)))
            else:
                mark = ""
        for key in realmark:
            service = "--Invalid--"
            for sname, idx in fwmarks.items():
                if key == idx:
                    service = sname
            if len(set(realmark[key])) != len(set(stasks[key])):
                print "Incorrect LB Programming for service %s" % service
                print "control-plane backend tasks:"
                for task in stasks[key]:
                    print task
                print "kernel IPVS backend tasks:"
                for task in realmark[key]:
                    print task
            else:
                print "service %s... OK" % service

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: ssd.py network-name [gossip-consistency]'
        sys.exit()

    cli = docker.APIClient(base_url='unix://var/run/docker.sock', version='auto')
    if len(sys.argv) == 3:
        command = sys.argv[2]
    else:
        command = 'default'

    if command == 'gossip-consistency':
        cspec = docker.types.ContainerSpec(
            image='sanimej/ssd',
            args=[sys.argv[1], 'gossip-hash'],
            mounts=[docker.types.Mount('/var/run/docker.sock', '/var/run/docker.sock', type='bind')]
        )
        mode = docker.types.ServiceMode(
            mode='global'
        )
        task_template = docker.types.TaskTemplate(cspec)

        cli.create_service(task_template, name='gossip-hash', mode=mode)
        #TODO change to a deterministic way to check if the service is up.
        time.sleep(5)
        output = cli.service_logs('gossip-hash', stdout=True, stderr=True, details=True)
        for line in output:
            print("Node id: %s gossip hash %s" % (line[line.find("=")+1:line.find(",")], line[line.find(" ")+1:]))
        if cli.remove_service('gossip-hash') is not True:
            print("Deleting gossip-hash service failed")
    elif command == 'gossip-hash':
        data = cli.inspect_network(sys.argv[1], verbose=True)
        services = data["Services"]
        md5 = hashlib.md5()
        entries = []
        for service, value in services.items():
            entries.append(service)
            entries.append(value["VIP"])
            for task in value["Tasks"]:
                for key, val in task.items():
                    if isinstance(val, dict):
                        for k, v in val.items():
                            entries.append(v)
                    else:
                        entries.append(val)
        entries.sort()
        for e in entries:
            md5.update(e)
        print(md5.hexdigest())
        sys.stdout.flush()
        while True:
           signal.pause()
    elif command == 'default':
        if sys.argv[1] == "ingress":
            check_network("ingress", ingress=True)
        else:
            check_network(sys.argv[1])
            check_network("ingress", ingress=True)
