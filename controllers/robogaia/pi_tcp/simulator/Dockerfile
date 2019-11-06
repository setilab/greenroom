FROM python:2.7.15
ENV PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin
RUN easy_install requests
WORKDIR /sim
COPY simulator /sim
COPY grclient.py /sim
CMD ["bash", "simulator"]
