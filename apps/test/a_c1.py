# Interestパケットを送信し、対応するDataパケットを受け取る側
import cefpyco
import time

def consumer():
    with cefpyco.create_handle() as handle:
        #interest_name = "ccnx:/hoge"
        interest_name = "ccnx:/test/data"
        print(f"Sending Interest for {interest_name}")
        handle.send_interest(interest_name, 0)

        start_time = time.time()
        while True:
            try:
                data = handle.receive()
                if data.is_data and data.name == interest_name:
                    rtt = time.time() - start_time
                    print(f"ALL DATA: \n{data}")
                    print(f"Received Data: {data.payload.decode()}")
                    print(f"Round Trip Time (RTT): {rtt:.4f} seconds")
                    break
            except KeyboardInterrupt:
                print("Consumer shutting down.")
                break

if __name__ == "__main__":
    consumer()

