ARG ubuntu_version=20.04
FROM ghcr.io/rse-ops/spack-ubuntu-libfabric:ubuntu-${ubuntu_version} as builder

ENV FI_EFA_USE_DEVICE_RDMA=1
ENV RDMAV_FORK_SAFE=1
ENV DEBIAN_FRONTEND=noninteractive


WORKDIR /code

# Python packages and script
COPY preprocess_radiographs.py /code

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    python3 \
    python3-pip

RUN python3 -m pip install --user numpy multiprocess opencv-python 
