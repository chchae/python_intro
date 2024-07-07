import threading
import time


class MyThread(threading.Thread) :
    def __init__(self, i: int ):
        super().__init__()
        self.x = i

    def run(self) :
        print( f"start: {self.x}" )
        time.sleep(1)
        print( f"end  : {self.x}" )


 
def main() -> None :
    t1 = MyThread(1)
    t1.start()
    t2 = MyThread(2)
    t2.start()


if __name__ == "__main__" :
    main()
       