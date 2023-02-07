ARG centos_version=latest
FROM centos:${centos_version}

RUN cd /etc/yum.repos.d/
RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-* && \
    sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*

WORKDIR /home/${USER}

# Python packages and script
COPY preprocess_radiographs.py /home/${USER}/.
RUN yum install -y mesa-libGL && \
    yum install -y python3
RUN python3 -m pip install -U --force-reinstall pip && \
    python3 -m pip install --user numpy multiprocess opencv-python 
