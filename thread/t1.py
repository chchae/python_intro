import threading
import time

counter = 0

def increment( id : int ) -> None:
    global counter
    print( f"{id}: start {counter:_}" )
    for _ in range(100_000):
        counter += 1
        time.sleep(0.0000001)
    print( f"{id}: end  {counter:_}" )


def main() -> None :
    threads: list[threading.Thread]= []
    for id in range(8):
        thread = threading.Thread(target=increment,args=(id,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("Final counter value:", counter)


if __name__ == "__main__" :
    main()
