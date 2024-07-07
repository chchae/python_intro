# run cpu-intensive external program concurrently using asyncio
# for RosettaFold

import random
from dataclasses import dataclass
from abc import ABC, abstractmethod
import multiprocessing
import threading


class SequenceFetcher(ABC) :
    _lock = threading.Lock()

    @abstractmethod
    async def fetch(sel) -> str | None :
        raise NotImplementedError()


class DummySequenceFetcher(SequenceFetcher) :

    def __init__(self) :
        self._seqs : list[int] = [ random.randint( 30, 42 ) for _ in range(200) ]

    async def fetch(self) -> str | None :
        async with self._lock:
            if len( self._seqs ) == 0 :
                return None
            return str( self._seqs.pop(0) )

class FileSequenceFetcher(SequenceFetcher) :
    async def fetch(self) -> str | None :
        raise NotImplementedError()

class OracleSequenceFetcher(SequenceFetcher) :
    async def fetch(self) -> str | None :
        raise NotImplementedError()


@dataclass
class ProteinBuilder(ABC) :
    jobid : int
    fetcher : SequenceFetcher
    future : asyncio.Future[ list[int] ]

    async def run(self) -> None :
        result: list[int] = []
        while True:
            if ( nseed := await self.fetcher.fetch() ) is None :
                break
            res = await self.build( int(nseed) )
            result.append( res )
        self.future.set_result(result)

    @abstractmethod
    async def build( self, nseed: int ) -> int :
        raise NotImplementedError()

@dataclass
class DummyProteinBuilder(ProteinBuilder) :
    jobid : int
    fetcher : SequenceFetcher
    future : asyncio.Future[ list[int] ]

    async def build( self, nseed: int ) -> int :
        print( f"start  : work {self.jobid = :2d}, {nseed = :2d}" )
        result = await self.run_builder( "/Users/chchae/bin/fibo" + " " + str(nseed) )
        print( f"finish : work {self.jobid = :2d}, {nseed = :2d}, {result = }" )
        return result

    @staticmethod
    async def run_builder(cmd: str) -> int:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if False :
            print( f"{proc.returncode = } {stdout.decode() = } {stderr.decode() = }" )
        result = int( stdout.decode() )
        return result



class RosettaFoldProteinBuilder(ProteinBuilder) :
    jobid : int
    fetcher : SequenceFetcher
    future : asyncio.Future[ list[int] ]

    async def build( self, nseed: int ) -> int :
        raise NotImplementedError()

class AlphaFoldProteinBuilder(ProteinBuilder) :
    jobid : int
    fetcher : SequenceFetcher
    future : asyncio.Future[ list[int] ]

    async def build( self, nseed: int ) -> int :
        raise NotImplementedError()


def main() -> None :
    MAX_WORKERS : int = multiprocessing.cpu_count()

    with ProcessPoolExecutor() as pex :
        lock = multiprocessing.Manager().Lock()
        fetcher = DummySequenceFetcher()


    loop = asyncio.get_running_loop()
    fetcher = DummySequenceFetcher()
    futures : list[ asyncio.Future[ list[int] ] ] = []
    for jobid in range(MAX_WORKERS) :
        future = loop.create_future()
        asyncio.create_task( DummyProteinBuilder( jobid, fetcher, future ).run() )
        futures.append( future )
            
    results: list[ list[int] ] = [ await future for future in futures ]
    reduced = sum( results, [] )
    print( f"result[{len(reduced)} = {reduced}]" )


if __name__ == "__main__" :
    main()
