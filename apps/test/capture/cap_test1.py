
# REQ:
# pip install pyshark
# sudo apt update
# sudo apt install wireshark tshark

import pyshark
import time

def capture_icn_traffic(interface="eth0", capture_duration=10, output_file="icn_capture.pcapng"):
    """
    指定されたネットワークインターフェースでICN (CCNx) 通信を一定時間キャプチャし、
    その内容をファイルに保存します。

    Args:
        interface (str): 監視するネットワークインターフェース名 (例: "eth0").
        capture_duration (int): キャプチャする時間 (秒).
        output_file (str): キャプチャ結果を保存するファイル名 (例: "icn_capture.pcapng").
    """
    try:
        print(f"ICN (CCNx) 通信を {interface} で {capture_duration} 秒間キャプチャします...")

        # CCNx プロトコルをフィルタリング
        capture = pyshark.LiveCapture(interface=interface, display_filter='ccnx',
                                      output_file=output_file)

        # 一定時間キャプチャを実行
        capture.sniff(timeout=capture_duration)

        print(f"キャプチャ終了。結果は {output_file} に保存されました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        if 'capture' in locals() and capture.is_capturing():
            capture.close()

if __name__ == "__main__":
    interface_to_monitor = "eth0"  # 監視するネットワークインターフェース名を設定 (適宜変更)
    capture_time = 20             # キャプチャする時間 (秒) を設定
    output_filename = "ccnx_capture_" + time.strftime("%Y%m%d_%H%M%S") + ".pcapng" # 出力ファイル名をタイムスタンプ付きにする

    capture_icn_traffic(interface=interface_to_monitor,
                         capture_duration=capture_time,
                         output_file=output_filename)
