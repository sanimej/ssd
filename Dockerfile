FROM ubuntu:16.04
MAINTAINER Santhosh Manohar <santhosh@docker.com>
RUN apt-get update && apt-get install -y \
        dnsutils \
        iptables \
        build-essential \
        dnsmasq \
        ipvsadm \
        iperf \
        curl \
        strace \
	util-linux \
	python-pip
ADD ssd.py /
RUN pip install docker
CMD [ "python", "./ssd.py"]
