import sys
import asyncio
import random
import time
import multiprocessing
from typing import AsyncGenerator, Coroutine, Callable
from itertools import groupby


async def dummy_protein_builder_closure( jobid: int ) -> Callable[[],int]:

    async def build_func() :
        nsleep = random.randint(0,5)
        print( f"{jobid} : start {nsleep}" )
        await asyncio.sleep( nsleep )
        print( f"{jobid} : end   {nsleep}" )
        return nsleep

    return build_func()



async def dummy_protein_builder_closure_1( jobid: int ) :
    print( f"{jobid} : start" )
    await asyncio.sleep(1)
    print( f"{jobid} : end" )
    return []



async def main() -> None :
    MAX_WORKERS : int = multiprocessing.cpu_count()
    start = time.perf_counter()

    async with asyncio.TaskGroup() as tg:
        #tasks = [ tg.create_task(  dummy_protein_builder_closure(id) ) for id in range(MAX_WORKERS) ]
        tasks : list[asyncio.Future] = []
        for id in range(MAX_WORKERS) :
            t = await dummy_protein_builder_closure(id)
            task = tg.create_task( t )
            tasks.append( task )

        #results = await tg
    results = [ task.result() for task in tasks ]
    
    #results = [ r for rs in results for r in rs ]
    print( f"\n{len(results)}-structures : {results}" )
    print( f"\nElapsed time {time.perf_counter() - start:.1f}" )


if __name__ == "__main__" :
    asyncio.run( main() )
