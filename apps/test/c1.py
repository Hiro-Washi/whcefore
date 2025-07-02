from time import sleep 
import cefpyco
import time

interest_stats = {}
data_stats = {}

with cefpyco.create_handle() as handle: 
  while True:
    content_name = "ccnx:/example/data"
    chunk_num = 0 # コンテンツを小単位に分割
    
    send_time = time.time()
    #handle.send_interest(content_name, chunk_num=chunk_num)
    handle.send_interest("ccnx:/test.txt", 0) 
    
    interest_key = (content_name, chunk_num)
    # 同じコンテンツの異なるチャンクに対するInterestパケットの送信回数を別々にカウントしたり、特定のコンテンツ・チャンクに対するInterestパケットの送信時刻を記録
    if interest_key not in interest_stats:
        interest_stats[interest_key] = {"send_times": []}
    interest_stats[interest_key]["send_times"].append(send_time)

    data =handle.receive() 
    print(data)
    

    if data:
        recv_time = time.time()
        recv_delay = recv_time - send_time
    
        data_key = (data.name, data.chunk_num)
        data_stats[data_key] = {
            "recv_time": recv_time,
            "recv_size": len(data.payload),
            "recv_delay": recv_delay,
        }

        print(f"Received data: {data.payload}")
        print(f"Receive delay: {recv_delay} seconds")
    else:
        print("Timeout or error occurred.")
    
    #if data.is_succeededand(data.name =="ccnx/test") and (data.chunk_num==0): 
    #  print("Success") 
    #  print(data) 
    #  break 
    #sleep(1)

print("Interest statistics:", interest_stats)
print("Data statistics:", data_stats)
