import random
import multiprocessing
from multiprocessing.synchronize import Lock as LockBase
from concurrent.futures import ProcessPoolExecutor, Future



def fibo(n : int) -> int :
    if n < 2 :
        return 1
    return fibo(n - 2) + fibo(n - 1)



class Counter(object):
    def __init__(self):
        # self.lock = threading.Lock()
        self.count = 0

    def increment(self):
        # with self.lock:
        self.count = self.count + 1
        print( f"count={self.count}" )

    def decrement(self):
        # with self.lock:
        self.count = self.count - 1
        print( f"count={self.count}" )


def increaser(counter: Counter):
    for _ in range(10):
        nseed = random.randint( 35, 40 )
        print( f'increase:start {nseed}' )
        fibo( nseed )
        print( f'increase:end   {nseed}' )
        #counter.increment()

def decreaser(counter: Counter):
    for _ in range(10):
        nseed = random.randint( 35, 40 )
        print( f'decrease:start {nseed}' )
        fibo( nseed )
        print( f'decrease:end   {nseed}' )
        #counter.decrement()



def worker(jobid : int, counter: Counter, lock: LockBase = None ):
    for _ in range(5):
        nseed = random.randint( 30, 40 )
        print( f'worker_{jobid}:start {nseed=}' )
        result = fibo( nseed )
        print( f'worker_{jobid}:end   {nseed=} {result=}' )
        if( lock ) :
            with lock:
                counter.increment()

def worker_a(jobid : int, counter: Counter, lock: LockBase ):
    for _ in range(5):
        nseed = random.randint( 30, 40 )
        fibo( nseed )


def main1() -> None :
    counter : Counter = Counter()
    lock : LockBase = multiprocessing.Lock()
    MAX_WORKERS : int = multiprocessing.cpu_count()
 
    processes = [ 
        multiprocessing.Process( 
            target=worker, args=(jobid, counter, lock) ) 
            for jobid in range(MAX_WORKERS) 
    ]
    for p in processes:
        p.start()
    for p in processes:
        p.join()



def main() -> None :
    MAX_WORKERS : int = multiprocessing.cpu_count()

    with ProcessPoolExecutor() as execp:
        counter : Counter = Counter()
        # lock : LockBase = multiprocessing.Lock()
        lock = multiprocessing.Manager().Lock()
        #futures : list[Future[Any]] = []
        for jobid in range(MAX_WORKERS) :
            execp.submit( worker, jobid, counter, lock )


if __name__ == "__main__" :
    main()
