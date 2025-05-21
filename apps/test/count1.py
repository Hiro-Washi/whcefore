import cefpyco
import time

prefix = "ccnx:/testdata"
sent_count = 0
sent_bytes = 0
received_count = 0
received_bytes = 0

with cefpyco.create_handle() as h:
    h.register(prefix)
    data = b"test data: asdfghjklqwertyuiopzxcvbnm1234567890" * 100
    chunk_size = 1024
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        h.send_data(prefix, chunk, i // chunk_size)
        sent_count += 1
        sent_bytes += len(chunk)
        time.sleep(0.1)

    print("--- 送信統計 ---")
    print(f"送信パケット数: {sent_count}")
    print(f"送信バイト数: {sent_bytes}")

    chunk_num = 0
    while True:
        h.send_interest(prefix, chunk_num)
        info = h.receive()
        if info and info.is_data and info.name.startswith(prefix):
            received_count += 1
            received_bytes += info.payload_len
            chunk_num += 1
        else:
            break

    print("\n--- 受信統計 ---")
    print(f"受信パケット数: {received_count}")
    print(f"受信バイト数: {received_bytes}")
