import asyncio
import numpy as np


NUM_PROC : int = 10

def get_sleeptime() -> int :
    return np.random.randint(2, 9)


async def fetch_data( id : int = 0, stime : int = 0 ) -> int :
    print( f"start fetching data id={id} dtime={stime}" )
    await asyncio.sleep( stime )
    print( f"end   fetching data id={id} dtime={stime}" )
    return stime


async def myfunc_1() -> None :
    tasks = []
    for id in range(NUM_PROC) :
        t = asyncio.create_task( fetch_data( id=1, stime=get_sleeptime() ) )
        tasks.append( t )

    for t in tasks :
        ret = await t
        print( ret )


async def myfunc_2() -> None :
    tasks = ( fetch_data( id=i, stime=get_sleeptime() ) for i in range(NUM_PROC) )
    results = await asyncio.gather( *tasks )
    for result in results:
        print( f"Received result: {result}" )


async def myfunc_3() :
    tasks = []
    async with asyncio.TaskGroup() as tg :
        for i in range(NUM_PROC) :
            task = tg.create_task( fetch_data( id=i, stime=get_sleeptime() ) )
            tasks.append( task )

    results = [ task.result() for task in tasks ]
    for result in results:
        print( f"Received result: {result}" )



def main() :
    asyncio.run( myfunc_3() )


if __name__ == "__main__" :
    main()

