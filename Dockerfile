FROM python:2.7.15-jessie
RUN easy_install web.py
RUN useradd -ms /bin/bash api
USER api
WORKDIR /api
COPY api /api
CMD ["python", "grapi.py"]
