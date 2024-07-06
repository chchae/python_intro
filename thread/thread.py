import random
from dataclasses import dataclass
from abc import ABC, abstractmethod
import threading
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import multiprocessing.synchronize
from multiprocessing.synchronize import Lock as LockBase


def fibo(n : int) -> int :
    if n < 2 :
        return 1
    return fibo(n - 2) + fibo(n - 1)


class SequenceFetcher(ABC) :
    @abstractmethod
    def fetch(sel) -> int :
        raise NotImplementedError()


class DummySequenceFetcher(SequenceFetcher) :
    def __init__(self) :
        self._seqs : list[int] = [ random.randint(30, 40) for _ in range(10) ]

    def fetch(self) -> int :
        if len( self._seqs ) == 0 :
            return -1
        return self._seqs.pop(0)

class FileSequenceFetcher(SequenceFetcher) :
    def fetch(self) -> int :
        raise NotImplementedError()

class OracleSequenceFetcher(SequenceFetcher) :
    def fetch(self) -> int :
        raise NotImplementedError()



@dataclass
class ProteinBuilder :
    jobid : int
    fetcher : SequenceFetcher
    #lock : LockBase
    lock : threading.Lock

    def __call__(self) :
        self.run()

    def run(self) -> None :
        while True:
            with self.lock :
                if (nseed := self.fetcher.fetch()) == -1 :
                    break
            self.build(nseed)

    def build( self, nseed: int ) -> None :
        print( f"start  : work {self.jobid = :2d}, {nseed = :3d}" )
        result = fibo(nseed)
        print( f"finish : work {self.jobid = :2d}, {nseed = :3d}, {result = }" )


def main_0() -> None :
    MAX_WORKERS : int = multiprocessing.cpu_count()
    print( f"{MAX_WORKERS = }" )

    lock : LockBase = multiprocessing.Lock()
    # lock : multiprocessing.synchronize.Lock = multiprocessing.Lock()
    fetcher = DummySequenceFetcher()
    processes = [ 
        multiprocessing.Process( target=ProteinBuilder(jobid, fetcher, lock) ) 
            for jobid in range(MAX_WORKERS) 
    ]
    for p in processes:
        p.start()
    for p in processes:
        p.join()

    print( f"Done" )


def main() -> None :
    MAX_WORKERS : int = multiprocessing.cpu_count()
    print( f"{MAX_WORKERS = }" )

    with ProcessPoolExecutor() as pex :
        lock = multiprocessing.Manager().Lock()
        fetcher = DummySequenceFetcher()
        for jobid in range(MAX_WORKERS) :
            pex.submit( ProteinBuilder(jobid, fetcher, lock) )

    print( f"Done" )


if __name__ == '__main__' :
    main()

