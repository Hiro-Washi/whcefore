FROM ubuntu:latest

RUN apt update && \
    apt -y upgrade && \
    DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
    sudo \
    libssh-dev \
    make \
    automake \
    build-essential \
    procps \
    zip \
    && rm -rf /var/lib/apt/lists/*

# ホストのユーザーUID/GIDを引数として受け取る（デフォルトは1000）
#ARG USER_ID=1000
#ARG GROUP_ID=1000
# ホストのGIDに合わせてグループを作成
#RUN groupadd -g ${GROUP_ID} dockeruser
# ホストのUID/GIDに合わせてユーザーを作成し、sudoグループに追加
# -m: ホームディレクトリを作成
# -s: デフォルトシェルをbashに設定
#RUN useradd -u ${USER_ID} -g ${GROUP_ID} -m -s /bin/bash -G sudo dockeruser
# 作成したユーザーがパスワードなしでsudoを実行できるように設定
#RUN echo "dockeruser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# これ以降のコマンドを実行するデフォルトユーザーをdockeruserに切り替え
#USER dockeruser
# whoamiを実行するとdockeruserと表示される?

#WORKDIR /tmp
#COPY v0.11.0.zip .
#RUN unzip v0.11.0.zip -d .
#WORKDIR cefore-0.11.0
WORKDIR /docker/cefore/whcefore
#USER dockeruser

# コンテナ起動時に実行されるデフォルトコマンド
CMD ["/bin/bash"]

#ENV CEFORE_DIR=/usr/local
#RUN aclocal && \
#    automake && \
#    ./configure --enable-csmgr --enable-cache && \
#    make && \
#    make install && \
#    ldconfig
