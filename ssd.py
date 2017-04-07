import docker
import re
import subprocess
import sys

ipv4match = re.compile(
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9]).' +
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9]).' +
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9]).' +
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])'
)


def get_namespaces(data, ingress=None):
    if ingress is not None:
        return ["/var/run/docker/netns/ingress_sbox"]
    else:
        spaces =[]
        sandboxes = {str(c) for c in data["Containers"]}
        for s in sandboxes:
            spaces.append(str(cli.inspect_container(s)["NetworkSettings"]["SandboxKey"]))
        return spaces


def check_network(nw_name, ingress=None):
    print "Verifying LB programming for containers on network %s" % nw_name

    data = cli.inspect_network(nw_name)

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
    print stasks

    spaces = get_namespaces(data, ingress)
    for s in spaces:
        ipvs = subprocess.check_output(['/usr/bin/nsenter', '--net=%s' % s, '/sbin/ipvsadm', '-ln'])

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
            if len(set(realmark[key])) != len(set(stasks[key])):
                for fw in fwmarks:
                    if key == fw:
                        service = fwmarks[fw]

                print "Incorrect LB Programming for service %s" % service
                print "control-plane backend tasks:"
                for task in stasks[key]:
                    print task
                print "kernel IPVS backend tasks:"
                for task in realmark[key]:
                    print task

if __name__ == '__main__':
    if len(sys.argv) is not 2:
        print 'Usage: ssd.py network-name'
        sys.exit()

    cli = docker.APIClient(base_url='unix://var/run/docker.sock')

    check_network(sys.argv[1])
    check_network("ingress", "true")