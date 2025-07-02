#!/bin/bash
docker run -it -d -w /app -v ./:/docker -h "test" --name "ceftest2" -p 9890:9896 linuxcontainers/debian-slim 
# IP: Docker のデフォルトブリッジネットワーク (docker0) は、通常、172.17.0.1/16 のIPアドレス範囲
docker build -t cefian:dev

(cd tmp)

apt update
apt upgrade
apt install -y libssh-dev make automake build-essential procps zip

cd /tmp
unzip /docker/v0.11.0.zip -d ./
cd cefore-0.11.0
export CEFORE_DIR=/usr/local
aclocal
automake
./configure --enable-csmgr --enable-cache
make
sudo make install

(echo "include $CEFORE_DIR/lib">> /etc/ld.so.conf)
ldconfig

sh /docker/init.sh 
# Unable to start csmgrd, Illegal CS_MODE=0


