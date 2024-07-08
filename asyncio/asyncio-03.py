import asyncio
import os
import random
import itertools
import time



async def makeitem( size : int = 5 ) -> str :
    return os.urandom( size ).hex()


async def random_sleep( caller=None ) -> None :
    i = random.randint( 0, 2 )
    if caller :
        print( f"{caller} sleeping for {i}-seconds" )
    await asyncio.sleep(i)


async def produce( name : int, q : asyncio.Queue ) -> None :
    n = random.randint( 0, 10 )
    for _ in itertools.repeat( None, n ) :
        await random_sleep( caller=f"Producer {name}" )
        i = await makeitem()
        t = time.perf_counter()
        await q.put( ( i, t ) )
        print( f"Producer {name} added <{i}> to queue." )


async def consume( name : int, q : asyncio.Queue ) -> None :
    while True :
        await random_sleep( caller=f"Consumer {name}" )
        i, t = await q.get()
        now = time.perf_counter()
        print( f"Consumer {name} got element <{i} in {now-t:0.5f} seconds" )
        q.task_done()



async def main() -> None :
    nprod = 2
    ncon = 5

    q = asyncio.Queue()
    producers = [ asyncio.create_task( produce(n,q) ) for n in range(nprod) ]
    consumers = [ asyncio.create_task( consume(n,q) ) for n in range(ncon) ]
    await asyncio.gather( *producers )
    await q.join()
    for c in consumers:
        c.cancel()


async def main1() -> None :
    print( "hello" )
    nprod = 2
    ncon = 5
    q = asyncio.Queue()
    producers = [ asyncio.create_task( produce(1,q)  ), asyncio.create_task( produce(2,q) ) ]
    consumers = [ asyncio.create_task( consume(1,q)  ), asyncio.create_task( consume(1,q)  ) ]
    await asyncio.gather( *producers )
    await q.join()
    for c in consumers:
        c.cancel()
    

if __name__ == "__main__" :
    asyncio.run( main() )


    # loop = nest_asyncio.get_running_loop()
    # loop = asyncio.get_running_loop()
    # await loop.create_task( main() )


