ARG ubuntu_version=focal
FROM fluxrm/flux-sched:${ubuntu_version}

ENV FI_EFA_USE_DEVICE_RDMA=1
ENV RDMAV_FORK_SAFE=1
ENV DEBIAN_FRONTEND=noninteractive

USER root
WORKDIR /code

# Python packages and script
COPY preprocess_radiographs.py /code

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    python3 \
    python3-pip \
    time

RUN pip install numpy multiprocess opencv-python 
