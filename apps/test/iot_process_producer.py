
# ICNネットワークの統計情報の取得（Not監視）と分析

import cefpyco
import time
import threading
import random
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class ICNProducer:
    def __init__(self, prefix_base="ccn:/iot/sensor", chunk_size=1024):
        self.prefix_base = prefix_base
        self.chunk_size = chunk_size
        self.data_store = {}  # データ格納（prefix -> list of chunks）
        self.stats = {
            "interest_received": 0,
            "data_sent": 0,
            "chunk_log": [],  # (prefix, chunk_num, size, timestamp)
        }

    def generate_sensor_data(self, sensor_id="001", data_size=4096):
        """センサーデータを仮生成してチャンク分割"""
        content = f"[{sensor_id}]センサー情報:{random.random()}".encode() * (data_size // 32)
        prefix = f"{self.prefix_base}/{sensor_id}/{int(time.time())}"
        chunks = [content[i:i+self.chunk_size] for i in range(0, len(content), self.chunk_size)]
        self.data_store[prefix] = chunks
        logging.info(f"センサーデータ生成: {prefix} ({len(chunks)}チャンク)")
        return prefix

    def listen_and_respond(self):
        """Interestを受信し、対応するチャンクを送信"""
        with cefpyco.create_handle() as h:
            logging.info("Producer起動: Interest待機中...")
            while True:
                info = h.receive()
                if info.is_interest:
                    self.stats["interest_received"] += 1
                    prefix = info.name
                    chunk_num = info.chunk_num or 0

                    if prefix in self.data_store and chunk_num < len(self.data_store[prefix]):
                        data = self.data_store[prefix][chunk_num]
                        h.send_data(prefix, data, chunk_num)
                        self.stats["data_sent"] += 1
                        self.stats["chunk_log"].append((prefix, chunk_num, len(data), datetime.now()))
                        logging.info(f"送信: {prefix} chunk={chunk_num} size={len(data)}")
                    else:
                        logging.warning(f"未対応Interest: {prefix} chunk={chunk_num}")

    def export_stats(self):
        """統計情報の出力"""
        print("\n=== 通信統計 ===")
        print(f"受信Interest数: {self.stats['interest_received']}")
        print(f"送信Data数     : {self.stats['data_sent']}")
        size_total = sum(s[2] for s in self.stats["chunk_log"])
        print(f"送信データ総量 : {size_total} bytes")
        print(f"平均チャンクサイズ: {size_total // max(1, self.stats['data_sent'])} bytes")

    def estimate_bandwidth(self):
        """ネットワーク帯域使用量の推定"""
        if len(self.stats["chunk_log"]) < 2:
            print("帯域推定不可: サンプルが少なすぎます。")
            return
        start = self.stats["chunk_log"][0][3]
        end = self.stats["chunk_log"][-1][3]
        elapsed = (end - start).total_seconds()
        total_bytes = sum(s[2] for s in self.stats["chunk_log"])
        bandwidth = total_bytes / elapsed if elapsed > 0 else 0
        print(f"帯域推定: {bandwidth:.2f} B/s ({bandwidth*8/1000:.2f} kbps)")

    def start(self):
        """データ生成と応答の両方を開始"""
        threading.Thread(target=self.listen_and_respond, daemon=True).start()
        while True:
            prefix = self.generate_sensor_data(sensor_id=str(random.randint(1, 5)), data_size=random.randint(2048, 8192))
            time.sleep(5)

if __name__ == "__main__":
    producer = ICNProducer()
    try:
        producer.start()
    except KeyboardInterrupt:
        producer.export_stats()
        producer.estimate_bandwidth()

