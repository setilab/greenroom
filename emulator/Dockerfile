FROM python:2.7.15
ENV PATH=/usr/local/bin:/bin:/usr/bin:/sbin:/usr/sbin
RUN easy_install requests
RUN useradd -ms /bin/bash cli
USER cli
WORKDIR /cli
COPY grcntrlrd.py /cli
COPY grclient.py /cli
CMD ["python", "grcntrlrd.py"]
