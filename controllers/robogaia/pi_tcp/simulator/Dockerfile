FROM python:3.5
ENV PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin
RUN pip3 requests
WORKDIR /sim
COPY simulator /sim
COPY grclient.py /sim
CMD ["bash", "simulator"]
