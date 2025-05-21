import cefpyco

prefix = "ccn:/iot/testdata"
chunk_num = 0
received_chunks = []
total_size = 0

with cefpyco.create_handle() as h:
    while True:
        h.send_interest(prefix, chunk_num)
        info = h.receive()
        if info.is_data and info.name == prefix and info.chunk_num == chunk_num:
            received_chunks.append(info.chunk_num)
            total_size += info.payload_len
            print(f"受信: Chunk {info.chunk_num}, サイズ: {info.payload_len} bytes")
            chunk_num += 1
        else:
            print("データの受信が終了または失敗")
            break

print("\n--- 結果 ---")
print(f"受信チャンク数: {len(received_chunks)}")
print(f"合計受信サイズ: {total_size} bytes")

