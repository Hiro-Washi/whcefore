# Dockerfile_debian_slim
FROM alpine:latest
LABEL description="Cefore v0.11.0 on Alpine latest"

ENV DEBIAN_FRONTEND=noninteractive
RUN apk add --update 
#RUN apt update && apt -y upgrade
#RUN apt update --fix-missing
RUN apk add \
    sudo \ # 9M
    libressl-dev \ # 16M
    make \ # <1M
    automake \ # 38M
    #build-essential \
    g++ \ # 226M
    procps \ # 2M
    autoconf \# 2M sh: autom4te: not found
    openssl # 1M  error: "OpenSSL3 is not installed."
    #zip \
    #unzip
# 293 M

#RUN rm -rf /var/lib/apt/lists/*

ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} dockeruser && useradd -u ${USER_ID} -g ${GROUP_ID} -m -s /bin/bash dockeruser
RUN mkdir -p /docker/workdir
RUN echo `ls -l /docker/workdir` >> /docker/ll.txt
RUN chown ${USER_ID}:${GROUP_ID} /docker/workdir
RUN echo `ls -l /docker/workdir` >> /docker/ll2.txt

WORKDIR /tmp
#RUN cp /docker/cefore/v0.11.0.zip .
#COPY v0.11.0.zip .
#RUN unzip v0.11.0.zip -d .
#RUN mv cefore-0.11.0 cefore

RUN cp -r /docker/cefore/cefore-0.11.0 /tmp
WORKDIR /tmp/cefore-0.11.0

#WORKDIR /docker/workdir
#USER dockeruser
#RUN echo `id && ls -l .` >> id.txt
# コンテナ起動時に実行されるデフォルトコマンド
#CMD ["/bin/bash"]

ENV CEFORE_DIR=/usr/local
RUN aclocal && \
    automake && \
    ./configure --enable-csmgr --enable-cache && \
    make && \
    make install && \
    ldconfig

RUN rm -rf /tmp/*
