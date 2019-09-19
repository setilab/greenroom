FROM python:2.7.15
ENV PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin
RUN easy_install requests
WORKDIR /gr
COPY mnt /gr
COPY grcntrlrd.py /gr
COPY grclient.py /gr
COPY config.json /gr
COPY mnt/bus.pseudo /gr/mnt/bus.pseudo
CMD ["python", "grcntrlrd.py", "-c", "config.json"]
