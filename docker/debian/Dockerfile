# Dockerfile_debian_slim
# docker build -t cefbian:test .

FROM linuxcontainers/debian-slim:latest
LABEL description="Cefore v0.11.0 on Debian Slim"

ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt -y upgrade
#RUN apt update --fix-missing
RUN apt install -y --no-install-recommends \
    sudo \
    libssl-dev \
    make \
    automake \
    build-essential \
    procps \
    #zip \
    unzip
#RUN rm -rf /var/lib/apt/lists/*

ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} dockeruser && useradd -u ${USER_ID} -g ${GROUP_ID} -m -s /bin/bash dockeruser
RUN mkdir -p /docker/workdir
RUN echo `ls -l /docker/workdir` >> /docker/ll.txt
RUN chown ${USER_ID}:${GROUP_ID} /docker/workdir
RUN echo `ls -l /docker/workdir` >> /docker/ll2.txt

WORKDIR /tmp
#RUN cp -r /docker/cefore/v0.11.0.zip .
COPY v0.11.0.zip .
RUN unzip v0.11.0.zip -d .
RUN mv cefore-0.11.0 cefore
WORKDIR cefore

#RUN cp -r /docker/cefore/cefore-0.11.0 /tmp
#COPY ./cefore-0.11.0 /tmp
#WORKDIR /tmp/cefore-0.11.0

#WORKDIR /docker/workdir
#USER dockeruser
#RUN echo `id && ls -l .` >> id.txt
# コンテナ起動時に実行されるデフォルトコマンド
#CMD ["/bin/bash"]

ENV CEFORE_DIR=/usr/local
RUN aclocal
RUN automake && \
    ./configure --enable-csmgr --enable-cache && \
    make && \
    make install && \
    ldconfig

#RUN rm -rf /tmp/*


COPY ./
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# コンテナ起動時に実行されるエントリーポイント
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
