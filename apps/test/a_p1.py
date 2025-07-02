#特定の名前空間のデータを提供する側
import cefpyco
import time

def producer():
    with cefpyco.create_handle() as handle:
        handle.register("ccnx:/test/data")
        print("Producer started, waiting for Interest packets...")
        while True:
            try:
                interest = handle.receive()
                if interest.is_interest:
                    print(f"Received Interest: {interest.name}")
                    response_data = f"Hello from Producer: {interest.name}".encode()
                    handle.send_data(interest.name, response_data, 0)
                    print(f"Sent Data packet for {interest.name}")
            except KeyboardInterrupt:
                print("Producer shutting down.")
                break

if __name__ == "__main__":
    producer()
