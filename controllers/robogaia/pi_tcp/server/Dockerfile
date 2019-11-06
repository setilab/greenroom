FROM python:3.5
ENV PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin
RUN pip3 requests
WORKDIR /gr
COPY grcntrlrd.py /gr
COPY config.json /gr
CMD ["python", "grcntrlrd.py"]
