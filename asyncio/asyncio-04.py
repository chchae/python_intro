import sys
import asyncio
import random
import time
import multiprocessing
from typing import AsyncGenerator

if sys.platform == "darwin":
    FIBO_EXE = "/Users/chchae/bin/fibo "
else:
    FIBO_EXE =  "/home/chchae/bin/fibo "


async def fetch_seed() -> AsyncGenerator[int,None] :
    seeds = [ random.randint( 40, 45 ) for _ in range(30) ]
    async def fetch() :
        for seed in seeds:
            yield seed
    return fetch()



async def worker_0( jobid: int, lock: asyncio.Lock, fetcher : AsyncGenerator[None,None] ) -> int :
    while True:
        async with lock:
            try:
                nseed = await anext(fetcher)
            except StopAsyncIteration :
                print( f"{jobid} : end of seed" )
                break

        _ = await do_something( FIBO_EXE + str(nseed) )
    return jobid
    


async def do_something( cmd: str ) -> int :
    #print( f"start: {cmd=}" )
    proc = await asyncio.create_subprocess_shell(
            cmd,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE
        )
    stdout, _ = await proc.communicate()
    ret = int( stdout.decode("utf-8") )
    #print( f"end  : {cmd=} {ret=}" )
    return ret


async def worker( jobid: int, lock: asyncio.Lock, fetcher : AsyncGenerator[None,None] ) -> list[int] :
    results = [ await do_something( FIBO_EXE + str(nseed) ) async for nseed in fetcher ]
    print( f"{jobid} : {results}" )
    return results



async def main() -> None :
    MAX_WORKERS : int = multiprocessing.cpu_count()
    start = time.perf_counter()

    lock = asyncio.Lock()
    fetcher = await fetch_seed()
    async with asyncio.TaskGroup() as tg:
        tasks = [ tg.create_task( worker(id, lock, fetcher) ) for id in range(MAX_WORKERS) ]
    results = [ task.result() for task in tasks ]
    print( results )
   
    print( f"Elapsed time {time.perf_counter() - start:.1f}" )


if __name__ == "__main__" :
    asyncio.run( main() )
