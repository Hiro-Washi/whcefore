#!/usr/bin/env python3
import cefpyco # 基本的な機能（ハンドルの作成、プレフィックスの登録、データの送信など）
import time

data = b"this is data for cefore" * 100  # 適当なサイズのByte列のデータ
chunk_size = 1024  # 1チャンクバイトサイズ
prefix = "ccnx:/iot/testdata"

with cefpyco.create_handle() as h:
    h.register(prefix) # 特定の名前空間のコンテンツを登録
    # 送信するデータ全体をチャンクサイズごとに分割するループ
    for i in range(0, len(data), chunk_size):
        chunk_data = data[i:i+chunk_size] # 現在チャンクのスライス操作
        chunk_num = i // chunk_size # 現在のチャンクのシーケンス番号。整数除算で各チャンクに0から始まる連続した番号を割り振る
        h.send_data(prefix, chunk_data, chunk_num)
        print(f"送信: Chunk {chunk_num}, サイズ: {len(chunk_data)} bytes")
        time.sleep(0.1)  # 応答性向上のため短めのスリープ

