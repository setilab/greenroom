FROM python:2.7.15
ENV PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin
WORKDIR /sim
COPY simulator /sim
COPY grclient.py /sim
COPY grcntrlrd.py /sim
COPY config.json /sim
CMD ["bash", "simulator", "summer"]
