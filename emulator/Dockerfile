FROM python:2.7.15
ENV PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin
RUN easy_install requests
WORKDIR /gr
COPY grcntrlrd.py /gr
COPY config.json /gr
COPY hold /gr
CMD ["bash", "hold"]
