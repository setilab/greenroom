FROM python:latest
ENV PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin
RUN pip install web.py redis
RUN useradd -ms /bin/bash api
USER api
WORKDIR /api
COPY grapi.py /api
CMD ["python", "grapi.py"]
