FROM python:latest
ENV PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin
RUN pip3 install web.py==0.40 redis
RUN useradd -ms /bin/bash api
USER api
WORKDIR /api
COPY grapi.py /api
CMD ["python", "grapi.py"]
