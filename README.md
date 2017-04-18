# ssd
Docker Swarm Service Driller
(Work In Progress)

ssd is a troubleshooting utility for swarm mode docker networks. ssd checks the 
consistency of the docker network control-plane state with what is programmed
in the kernel space.

As an example: Output below shows ssd checking for the load balancer programming on
network `nw` and reporting the status

````bash
user@net16-1:~/ssd# python ssd.py nw1
Verifying LB programming for containers on network ov1
Verifying container /s1.3.4czmztrsmuz13nbuw2xippyy6... OK
Verifying container /s1.2.1ezoscj06ebffixy4mye3n9yb... Incorrect LB Programming for service s1
control-plane backend tasks:
10.0.0.3
10.0.0.4
10.0.0.5
kernel IPVS backend tasks:
10.0.0.4
10.0.0.5
Verifying container /s1.1.jroe5ynyj15fyucfq10n8a0ra... OK
Verifying LB programming for containers on network ingress
Verifying container Ingress... OK
````

ssd is active WIP right now and will be available to run as a container when its complete.
