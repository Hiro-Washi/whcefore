import asyncio
import cefpyco
import time
import os
import csv
import datetime
import logging
from collections import deque
import json
import shutil # ディレクトリ削除用

# --- ロギング設定 ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("qam_monitoring.log"),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)

# --- 設定パラメータ ---
MONITOR_URI_PREFIX = "/your/content/name"  # 監視対象のコンテンツURIのプレフィックス
FACE_ID = 0  # CefpycoのFace ID (通常0でよい)
UPDATE_INTERVAL_SEC = 1  # now_stat.csv を更新する間隔 (秒)
RECORD_INTERVAL_HOURS = 1 # 監視記録ファイルを切り替える間隔 (時間)
DATA_RETENTION_DAYS = 3 # 過去データを保持する日数
MONITORING_DIR = "./monitoring" # 監視記録を保存するルートディレクトリ

# --- グローバル変数 (統計情報) ---
# 現在の統計
current_stats = {
    "timestamp": None,
    "interest_sent_count": 0,
    "interest_sent_bytes": 0,
    "data_received_count": 0,
    "data_received_bytes": 0,
    "data_receive_rate_bps": 0, # bits per second
    "data_receive_rate_pps": 0, # packets per second
    "avg_latency_ms": 0, # 平均遅延 (ミリ秒)
    "jitter_ms": 0,      # ジッター (ミリ秒)
    "bandwidth_usage_percent": 0 # 帯域使用率 (%)
}

# 監視対象コンテンツごとの統計（コンテンツ完了時などに記録）
content_stats = {} # key: content_name (Interest URI), value: dict of stats

# 遅延計算のためのInterest送信時刻記録
interest_timestamps = {} # key: Interest nonce, value: send_time

# ジッター計算のためのData受信時刻記録
# 連続するデータパケットのタイムスタンプを保持
data_reception_times = deque(maxlen=100) # 最近100個のデータパケット受信時刻を保持

# 帯域幅計算用
last_data_bytes = 0
last_data_time = time.time()
network_interface_bandwidth_mbps = 1000 # ネットワークインターフェースの理論帯域幅 (Mbps) - 環境に合わせて変更

# --- 補助関数 ---

def get_current_filename_prefix(base_dir=MONITORING_DIR):
    """現在の時刻に基づいてファイル名のプレフィックスを生成します。"""
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    hour_str = now.strftime("%H")
    
    dir_path = os.path.join(base_dir, date_str)
    os.makedirs(dir_path, exist_ok=True)
    
    return os.path.join(dir_path, f"{hour_str}")

def write_csv_header(filepath, stats_dict):
    """CSVファイルのヘッダーを書き込みます。"""
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(stats_dict.keys())

def append_to_csv(filepath, stats_dict):
    """CSVファイルに1行データを追記します。"""
    with open(filepath, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(stats_dict.values())

def get_data_packet_name_prefix(name):
    """
    データパケット名からコンテンツURIプレフィックスを取得します。
    例: /a/b/c/s=0 -> /a/b/c
    実際のNDNのセグメント名規則に合わせて調整してください。
    """
    parts = name.split('/')
    # セグメント情報がある場合、それを除去
    if parts and (parts[-1].startswith('s=') or parts[-1].startswith('%FD%00%00%01')): # Assuming NDN naming convention for segments (e.g., /<base>/<segment_num> or /<base>/%FD%00%00%01/<segment_num>)
        # より堅牢なプレフィックス抽出ロジックが必要な場合はここを修正
        # 例: /a/b/c/seg0 or /a/b/c/%FD%00%00%01/0
        #ここでは単純に最後のコンポーネントがセグメントと仮定
        name_prefix = '/'.join(parts[:-1])
    else:
        name_prefix = name
    
    # 監視対象URIのプレフィックスに合致するかどうかを確認する
    if name_prefix.startswith(MONITOR_URI_PREFIX):
        return name_prefix
    return None


# --- 統計計算ロジック ---

async def update_realtime_stats():
    """
    現在の統計情報を定期的に更新し、now_stat.csv に保存します。
    """
    global current_stats, last_data_bytes, last_data_time

    while True:
        await asyncio.sleep(UPDATE_INTERVAL_SEC)

        now = time.time()
        
        # 帯域幅の計算 (bits/sec)
        time_diff = now - last_data_time
        if time_diff > 0:
            data_rate_bps = (current_stats["data_received_bytes"] * 8) / time_diff
            data_rate_pps = current_stats["data_received_count"] / time_diff
            
            # 帯域使用率の計算 (%)
            # 理論帯域幅 (bps) に変換
            network_bandwidth_bps = network_interface_bandwidth_mbps * 1_000_000
            bandwidth_usage = (data_rate_bps / network_bandwidth_bps) * 100 if network_bandwidth_bps > 0 else 0

            current_stats["data_receive_rate_bps"] = data_rate_bps
            current_stats["data_receive_rate_pps"] = data_rate_pps
            current_stats["bandwidth_usage_percent"] = min(bandwidth_usage, 100.0) # 100%を超えないように
        
        # ジッターの計算 (ms)
        if len(data_reception_times) >= 2:
            intervals = np.diff(list(data_reception_times)) * 1000 # ミリ秒に変換
            current_stats["jitter_ms"] = np.std(intervals) if len(intervals) > 0 else 0
        else:
            current_stats["jitter_ms"] = 0

        # now_stat.csv へ保存
        current_stats["timestamp"] = datetime.datetime.now().isoformat()
        now_stat_filepath = "./now_stat.csv"
        
        try:
            write_csv_header(now_stat_filepath, current_stats)
            with open(now_stat_filepath, 'w', newline='') as f: # 常に上書き
                writer = csv.writer(f)
                writer.writerow(current_stats.keys())
                writer.writerow(current_stats.values())
            logger.debug(f"now_stat.csv updated: {json.dumps(current_stats)}")
        except Exception as e:
            logger.error(f"Failed to write now_stat.csv: {e}")

        # 次の期間の計算のためにリセット (差分計算用)
        last_data_bytes = current_stats["data_received_bytes"]
        last_data_time = now
        
        # 各種カウンターはゼロリセットしない (累積値を表示するため)。
        # 帯域幅やPPSは、あくまで直近1秒間のレートとして算出される。

def reset_per_content_stats(uri_prefix):
    """新しいコンテンツの統計情報を初期化します。"""
    content_stats[uri_prefix] = {
        "start_time": time.time(),
        "end_time": None,
        "total_interest_sent_count": 0,
        "total_interest_sent_bytes": 0,
        "total_data_received_count": 0,
        "total_data_received_bytes": 0,
        "content_delivery_time_ms": 0, # コンテンツ全体の遅延
        "avg_data_rate_bps": 0,
        "avg_latency_ms": 0,
        "jitter_ms": 0,
        "data_segment_latencies": [], # 各データセグメントの遅延リスト
        "data_reception_times": deque(maxlen=1000) # このコンテンツのための受信時刻
    }
    logger.info(f"Initialized stats for new content: {uri_prefix}")


# --- Cefpyco イベントハンドラ ---

async def handle_cefpyco_events(loop):
    """
    Cefpycoのイベントを処理するコルーチン。
    Interest送信、Data受信、NACK/CS_MISSなど。
    """
    global current_stats, content_stats, interest_timestamps, data_reception_times

    with cefpyco.CefpycoHandle() as handle:
        handle.set_log_level(3) # Cefpycoのログレベルを設定 (0:None, 1:Error, 2:Warn, 3:Info, 4:Debug)
        handle.register(MONITOR_URI_PREFIX) # 監視対象のURIを登録

        logger.info(f"Cefpyco node initialized. Monitoring URI prefix: {MONITOR_URI_PREFIX}")

        while True:
            info = handle.receive()
            if info.is_succeeded:
                if info.is_interest:
                    # ここでは自身がInterestを送信する側の統計を監視するため、
                    # 受信したInterestは通常無視するか、特別なロジックで処理する。
                    # コンテンツ提供者として動作する場合にのみ意味がある。
                    pass # 例: logger.debug(f"Received Interest: {info.name}")

                elif info.is_data:
                    data_name = info.name
                    data_payload_size = info.payload_len
                    reception_time = time.time()

                    logger.debug(f"Received Data: Name={data_name}, Size={data_payload_size} bytes")

                    # グローバル統計の更新
                    current_stats["data_received_count"] += 1
                    current_stats["data_received_bytes"] += data_payload_size

                    # Interest送信時刻との差分で遅延を計算
                    if info.name in interest_timestamps: # より正確にはNonceで紐付けるべき
                        latency = (reception_time - interest_timestamps.pop(info.name)) * 1000 # ミリ秒
                        
                        # グローバル統計の平均遅延を更新 (移動平均など)
                        if current_stats["avg_latency_ms"] == 0:
                            current_stats["avg_latency_ms"] = latency
                        else:
                            # 簡易的な移動平均 (より複雑なフィルタリングも可能)
                            current_stats["avg_latency_ms"] = (current_stats["avg_latency_ms"] * 0.9 + latency * 0.1)

                        # コンテンツごとの統計を更新
                        content_prefix = get_data_packet_name_prefix(data_name)
                        if content_prefix and content_prefix in content_stats:
                            content_stats[content_prefix]["data_segment_latencies"].append(latency)
                            content_stats[content_prefix]["total_data_received_count"] += 1
                            content_stats[content_prefix]["total_data_received_bytes"] += data_payload_size
                            content_stats[content_prefix]["data_reception_times"].append(reception_time)
                        
                    # ジッター計算用に受信時刻を記録
                    data_reception_times.append(reception_time)

                elif info.is_nack:
                    logger.warning(f"Received NACK for Interest (Nonce: {info.nonce})")
                    # Interest送信時刻リストから該当Interestを削除
                    for name, ts in list(interest_timestamps.items()):
                        if info.name == name: # より堅牢なNonceでの検索が必要
                            interest_timestamps.pop(name)
                            break
                    
                elif info.is_cs_miss:
                    logger.info(f"CS_MISS for Interest (Nonce: {info.nonce})")
                    # CS_MISSもNACKと同様に処理することが多い
                    for name, ts in list(interest_timestamps.items()):
                        if info.name == name: # より堅牢なNonceでの検索が必要
                            interest_timestamps.pop(name)
                            break

            # Cefpycoのイベントループをブロックしないように、少し待機
            await asyncio.sleep(0.001) # 1ms待機

async def send_interests_periodically():
    """
    監視対象のURIにInterestを定期的に送信します。
    ここではデモのため、単純なシーケンシャルなセグメントをリクエストします。
    """
    global current_stats, interest_timestamps, content_stats
    
    segment_num = 0
    # ここでは便宜上、無限にInterestを送信し続けます。
    # 実際の実験では、特定のコンテンツの全セグメントを要求するロジックを実装します。
    
    with cefpyco.CefpycoHandle() as handle:
        while True:
            # 各セグメントのリクエストを想定
            request_uri = f"{MONITOR_URI_PREFIX}/s={segment_num}" # NDNのセグメント命名規則に合わせる
            
            # ContentObjectの名前は通常、Interestの名前と同じではないので注意
            # CefpycoはInterestのNonceで対応づけるのが一般的
            # ここではシンプルにするためInterestの名前もURIとして保持
            interest_send_time = time.time()
            try:
                handle.send_interest(request_uri, lifetime=4000) # lifetimeを長めに設定
                current_stats["interest_sent_count"] += 1
                current_stats["interest_sent_bytes"] += len(request_uri.encode('utf-8')) # URIのバイト数を概算
                interest_timestamps[request_uri] = interest_send_time # InterestのURIをキーとしてタイムスタンプを保存
                logger.debug(f"Sent Interest: {request_uri}")

                # 新しいコンテンツの開始を検出 (簡易的な判定)
                if request_uri.endswith('/s=0'): # /s=0 で新しいコンテンツの要求開始とみなす
                    reset_per_content_stats(MONITOR_URI_PREFIX) # このデモではプレフィックス全体をコンテンツ名とする

            except Exception as e:
                logger.error(f"Failed to send Interest: {e}")

            segment_num += 1
            # 実際のアプリケーションでは、コンテンツの総セグメント数を知るか、
            # Timeout/NACKを受けて再送または終了するロジックが必要
            await asyncio.sleep(0.1) # Interest送信間隔 (調整可能)


# --- 監視記録の保存と整理 ---

async def manage_monitoring_records():
    """
    監視記録を定期的に保存し、古いデータを削除します。
    """
    last_record_hour = datetime.datetime.now().hour
    
    while True:
        await asyncio.sleep(60) # 1分ごとにチェック

        # 時間ごとのファイル切り替え
        current_hour = datetime.datetime.now().hour
        if current_hour != last_record_hour:
            logger.info(f"Time for new record file. Current hour: {current_hour}, Last record hour: {last_record_hour}")
            # ここで、直前の時間のコンテンツ統計を集計し、ファイルに書き込む
            # このデモでは、コンテンツ完了時に記録するため、特別な集計は行わないが、
            # もし時間ごとの集計が必要ならここにロジックを追加
            last_record_hour = current_hour

        # 古いディレクトリの削除
        delete_old_records()

def record_content_completion(uri_prefix):
    """
    コンテンツの受信完了時に統計情報を記録します。
    ここでは、Interest-Dataの対応を追跡し、最後のData受信時に呼び出すことを想定。
    """
    if uri_prefix not in content_stats:
        logger.warning(f"No stats found for completed content: {uri_prefix}")
        return

    stats = content_stats[uri_prefix]
    stats["end_time"] = time.time()
    
    if stats["start_time"] is not None and stats["end_time"] is not None:
        stats["content_delivery_time_ms"] = (stats["end_time"] - stats["start_time"]) * 1000
    
    # 平均データレート計算
    if stats["content_delivery_time_ms"] > 0:
        stats["avg_data_rate_bps"] = (stats["total_data_received_bytes"] * 8) / (stats["content_delivery_time_ms"] / 1000)

    # 平均遅延計算
    if stats["data_segment_latencies"]:
        stats["avg_latency_ms"] = np.mean(stats["data_segment_latencies"])

    # ジッター計算
    if len(stats["data_reception_times"]) >= 2:
        intervals = np.diff(list(stats["data_reception_times"])) * 1000 # ミリ秒
        stats["jitter_ms"] = np.std(intervals) if len(intervals) > 0 else 0

    # 記録ファイルへの保存
    filename_prefix = get_current_filename_prefix()
    record_filepath = f"{filename_prefix}.csv" # 時間ごとのファイル
    
    try:
        # ヘッダーを書き込む（ファイルが存在しない場合のみ）
        write_csv_header(record_filepath, stats)
        # データを追記
        append_to_csv(record_filepath, stats)
        logger.info(f"Recorded content stats for {uri_prefix} to {record_filepath}")
    except Exception as e:
        logger.error(f"Failed to record content stats to CSV: {e}")

    # 記録後、そのコンテンツの統計をリセット（次の通信のために）
    del content_stats[uri_prefix]


def delete_old_records():
    """
    指定日数以上経過した古い監視記録ディレクトリを削除します。
    """
    now = datetime.datetime.now()
    
    if not os.path.exists(MONITORING_DIR):
        return

    for dir_name in os.listdir(MONITORING_DIR):
        dir_path = os.path.join(MONITORING_DIR, dir_name)
        if os.path.isdir(dir_path):
            try:
                # ディレクトリ名から日付を解析 (例: "2023-10-26")
                dir_date = datetime.datetime.strptime(dir_name, "%Y-%m-%d")
                
                # 指定日数以上経過しているかチェック
                if (now - dir_date).days > DATA_RETENTION_DAYS:
                    logger.info(f"Deleting old monitoring directory: {dir_path}")
                    shutil.rmtree(dir_path)
            except ValueError:
                logger.warning(f"Skipping non-date directory: {dir_path}")
            except Exception as e:
                logger.error(f"Error deleting directory {dir_path}: {e}")

# --- メイン関数 ---

async def main():
    """
    すべての非同期タスクを起動します。
    """
    logger.info("Starting QAM Monitoring Node...")

    # 各ディレクトリを確実に作成
    os.makedirs(MONITORING_DIR, exist_ok=True)

    # 非同期タスクの起動
    tasks = [
        asyncio.create_task(handle_cefpyco_events(asyncio.get_event_loop())),
        asyncio.create_task(update_realtime_stats()),
        asyncio.create_task(manage_monitoring_records()),
        asyncio.create_task(send_interests_periodically()) # デモ用: Interestを定期的に送信
    ]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Monitoring tasks cancelled.")
    except Exception as e:
        logger.critical(f"An unhandled error occurred in main: {e}")
    finally:
        logger.info("QAM Monitoring Node stopped.")


if __name__ == "__main__":
    # Content Completionのトリガーをシミュレートする例
    # 実際のアプリケーションでは、コンテンツの最後のセグメントを受信した際に
    # この関数を呼び出すロジックが必要になります。
    # 例: handle_cefpyco_events内で、受信したデータがコンテンツの最終セグメントであることを検知し、
    # asyncio.get_event_loop().call_soon_threadsafe(record_content_completion, content_prefix)
    # のように呼び出す。

    # Cefpycoは通常、スレッドセーフではないため、
    # handle_cefpyco_eventsはCefpycoHandleと同じスレッド/asyncioループで実行する必要があります。
    # send_interests_periodicallyも同様。
    # update_realtime_stats と manage_monitoring_records は独立して実行できます。

    # デモとして、ここでは Interest を自動的に送信し、データを受信したら統計を更新する。
    # コンテンツの完了検出は、実際のNDNアプリケーションのロジックに依存します。
    # 例: /your/content/name/s=0, /your/content/name/s=1, ..., /your/content/name/s=<last_segment_num>
    # といった順序で受信し、最後のセグメントを受信したら content_stats の該当エントリを確定させる。

    # asyncioを起動
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Monitoring node stopped by user (Ctrl+C).")
