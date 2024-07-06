# run cpu-intensive external program concurrently using asyncio
# for RosettaFold

import asyncio
import multiprocessing
import random


g_seed : list[int] = [ random.randint( 35, 45 ) for _ in range(100) ]
def fetch_data() -> int :
    if len(g_seed) == 0 :
        return -1
    return g_seed.pop(0)



async def run(cmd: str) -> int:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stderr=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    # print( f"{proc.returncode = } {stdout.decode() = } {stderr.decode() = }" )
    result = int( stdout.decode() )
    return result


async def process(jobid: int) -> int :
    for _ in range(10) :
        nseed = random.randint( 35, 45 )
        result = await run( "/Users/chchae/bin/fibo" + " " + str(nseed) )
        print( f"{jobid = :2d} : {nseed = :3d}, {result = }" )
    return jobid


async def main_0() -> None:
    MAX_WORKERS : int = multiprocessing.cpu_count()
    tasks = [ asyncio.create_task( process(id) ) for id in range(MAX_WORKERS) ]
    results = [ await t for t in tasks ]
    print( results )


async def main_1() -> None:
    MAX_WORKERS : int = multiprocessing.cpu_count()
    tasks = [ process(id) for id in range(MAX_WORKERS) ]
    results = await asyncio.gather( *tasks )
    print( results )


async def main_taskgroup() -> None:
    MAX_WORKERS : int = multiprocessing.cpu_count()
    async with asyncio.TaskGroup() as tg:
        tasks = [ tg.create_task( process(id) ) for id in range(MAX_WORKERS) ]
    results = [ t.result() for t in tasks ]
    print( results )


async def process(jobid: int, future, lock) -> int :
    while True :
        #nseed = random.randint( 35, 45 )
        async with lock:
            if ( nseed := fetch_data() ) == -1 :
                break
        result = await run( "/Users/chchae/bin/fibo" + " " + str(nseed) )
        print( f"{jobid = :2d} : {nseed = :3d}, {result = }" )

    future.set_result(jobid)
    return jobid


async def main_future() -> None:
    MAX_WORKERS : int = multiprocessing.cpu_count()
    lock = asyncio.Lock()
    loop = asyncio.get_running_loop()
    futures : list[asyncio.Future] = []
    for id in range(MAX_WORKERS) :
        future = loop.create_future()
        asyncio.create_task( process(id, future, lock) )
        futures.append( future )

    results = [ await future for future in futures ]
    print( f"{results}" )


if __name__ == "__main__" :
    asyncio.run( main_future() )
