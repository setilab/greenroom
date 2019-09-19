FROM ubuntu
ENV PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin
WORKDIR /sim
ADD mnt /sim
COPY simulator /sim
CMD ["bash", "simulator"]
