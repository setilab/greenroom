FROM python:2.7-alpine
RUN easy_install web.py
RUN useradd -ms /bin/bash pi
USER pi
WORKDIR /api
COPY api /api
CMD ["python", "grapi.py"]
