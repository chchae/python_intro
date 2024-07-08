import sys
import concurrent.futures
from random import randint
from typing import Generator

if sys.platform == "darwin":
    FIBO_EXE = "/Users/chchae/bin/fibo "
else:
    FIBO_EXE =  "/home/chchae/bin/fibo "

seeds : Generator[int, None, None] = ( randint(38, 45) for _ in range(100) )


def thread_func( nseed: int ) -> int :
    import subprocess
    jobid = 0
    print( f"start  : {jobid = :2d}, {nseed = :2d}" )
    cmd = "/Users/chchae/bin/fibo " + str(nseed)
    ret = subprocess.check_output( cmd, shell=True ).decode("utf-8")
    print( f"finish : {jobid = :2d}, {nseed = :2d}, {ret = }" )
    return int(ret)


def main() -> None :
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map( thread_func, seeds )

    print( list(results) )


if __name__ == "__main__" :
    main()

