FROM python:2.7.15
ENV PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin
RUN easy_install web.py redis
RUN useradd -ms /bin/bash api
USER api
WORKDIR /api
COPY grapi.py /api
CMD ["python", "grapi.py"]
