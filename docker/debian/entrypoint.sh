#!/bin/bash

# コンテナのタイプ (router, producer, consumer) を環境変数から取得
NODE_TYPE=${NODE_TYPE:-"unknown"}
# コンテナ名 (Hostname) をノード名として使用
NODE_NAME=${HOSTNAME}

echo "Ceforeノードを開始します: ${NODE_NAME} (タイプ: ${NODE_TYPE})"

# Ceforeデーモンの設定ファイルパス
CEFORE_CONF="/usr/local/cefore/cefnetd.conf"

# 共通のCefore設定
cat <<EOF > "${CEFORE_CONF}"
#log_level debug # ログレベルをデバッグに設定
NODE_NAME="${NODE_NAME}"
CEF_LOG_LEVEL=2
#PORT_NUM=9896
#LOCAL_SOCK_ID=0
#CSMGR_NODE=127.0.0.1
CSMGR_PORT_NUM=9799
#PIT_SIZE=65535
#PIT_SIZE_APP=64
#FIB_SIZE=1024
#FIB_SIZE_APP=64
CS_MODE=1
#LOCAL_CACHE_CAPACITY=65535
#LOCAL_CACHE_INTERVAL=60

CEF_DEBUG_LEVEL=3
EOF

echo "Ceforeデーモンを開始します..."
# cefore_daemonをバックグラウンドで起動
#/usr/local/bin/cefore_daemon -f "${CEFORE_CONF}" &
/docker/cefore/whcefore/bash/init.sh
CEFORE_PID=$!
echo "CeforeデーモンがPID: ${CEFORE_PID} で開始されました"

# Ceforeデーモンが完全に起動するまで少し待機
sleep 2

# 各ノードタイプに応じたFace/FIB設定
if [ "${NODE_TYPE}" == "router" ]; then
    echo "ルーターノードを設定します: ${NODE_NAME}"
    # プロデューサーとコンシューマーへのFaceを作成
    # IPアドレスはdocker-compose.ymlで定義されたものを使用
    sudo cefroute add ccnx:/test udp 172.18.0.21 # producer1
    sudo cefroute add ccnx:/test udp 172.18.0.31 # consumer1
    sudo cefroute add ccnx:/test udp 172.18.0.32 # consumer2
    
    sleep 1 # Faceが完全に確立するのを少し待つ
    
    # producer1へのFace IDを動的に取得
    PRODUCER_FACE_ID=$(/usr/local/bin/cefnetd_show_faces | grep "udp 172.18.0.21" | awk '{print $NF}')
    
    if [ -n "${PRODUCER_FACE_ID}" ]; then
        echo "ccnx:/video/stream へのFIBエントリをFace ID: ${PRODUCER_FACE_ID} 経由で追加します。"
        # "ccnx:/video/stream" のInterestをproducer1 (Face ID: PRODUCER_FACE_ID) へ転送するFIBを設定
        /usr/local/bin/cefnetd_add_fib_entry ccnx:/video/stream "${PRODUCER_FACE_ID}"
    else
        echo "producer1 (172.18.0.21) へのFace IDが見つかりませんでした。FIBエントリは追加されません。"
    fi

elif [ "${NODE_TYPE}" == "producer" ]; then
    echo "プロデューサーノードを設定します: ${NODE_NAME}"
    # プロデューサーはルーターへのFaceを作成します
    sudo cefroute add ccnx:/test udp 172.18.0.11 # router1
    
    echo "プレースホルダー: 映像配信アプリケーションを開始します..."
    # ここに映像配信アプリケーションの起動コマンドを記述します。
    # 例: python3 /app/video_producer.py &
    # Webカメラデバイスがマウントされている場合、fswebcamでテスト撮影
    if [ -c /dev/video0 ]; then
        echo "Webカメラ(/dev/video0) が利用可能です。テスト撮影します..."
        echo `ls -l /dev/video*`
        #fswebcam -r 640x480 --no-banner /tmp/test_image.jpg
        echo "テスト画像が /tmp/test_image.jpg に保存されました。"
    else
        echo "Webカメラ(/dev/video0) は利用できません。"
    fi

elif [ "${NODE_TYPE}" == "consumer" ]; then
    echo "コンシューマーノードを設定します: ${NODE_NAME}"
    # コンシューマーはルーターへのFaceを作成します
    sudo cefroute add ccnx:/test udp 172.18.0.11 # router1
    
    echo "プレースホルダー: 映像受信アプリケーションを開始します..."
    # ここに映像受信アプリケーションの起動コマンドを記述します。
    # 例: python3 /app/video_consumer.py &

else
    echo "不明なノードタイプです: ${NODE_TYPE}"
    exit 1
fi

echo "すべての初期設定が完了しました。"
echo "Ceforeデーモン (PID: ${CEFORE_PID}) がフォアグラウンドで実行されるように待機します。"
# Ceforeデーモンプロセスが終了するまでコンテナを維持
wait "${CEFORE_PID}"
