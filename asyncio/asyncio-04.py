import sys
import asyncio
import random
import time
import multiprocessing
from typing import AsyncGenerator, Coroutine
from itertools import groupby


if sys.platform == "darwin":
    FASTA_DATA = "/Users/chchae/work/data/sequence-short.fasta"
    FIBO_EXE = "/Users/chchae/bin/fibo "
else:
    FASTA_DATA = "/home/chchae/work/data/sequence-short.fasta"
    FIBO_EXE =  "/home/chchae/bin/fibo "


type SequenceFasta = tuple[ str, str, str ]


async def fetch_seed( lock: asyncio.Lock ) -> AsyncGenerator[int,None] :
    seeds = [ random.randint( 30, 40 ) for _ in range(1000) ]
    async def fetch() -> AsyncGenerator[int,None] :
        for seed in seeds:
            async with lock:
                yield seed
    return fetch()


async def dummy_sequence_fetch_closure( lock: asyncio.Lock, length: int = 128, count: int = 100 ) -> AsyncGenerator[SequenceFasta,None] :
    _seqs : list[str] = [
        ''.join( random.choices( "ACDEFGHIKLMPQRSTVWY", k=length ) ) for _ in range(count)
    ]

    async def fetch_func() -> AsyncGenerator[SequenceFasta,None] :
        for id in _seqs:
            async with lock:
                yield (id, id, id)

    return fetch_func()


async def fasta_sequence_fetch_closure( filename : str, lock: asyncio.Lock ) -> AsyncGenerator[SequenceFasta,None] :
    async def fetch_func() -> AsyncGenerator[SequenceFasta,None] :
        with open( filename ) as ifp :
            lines = ( x[1] for x in groupby(ifp, lambda line: str(line).startswith(">") ) )
            for header in lines:
                headerStr = str(header.__next__())
                (name, descr) = headerStr[1:].strip().split( '|', 1 )
                seq = "".join( s.strip() for s in lines.__next__() )
                async with lock:
                    yield ( name.strip(), descr.strip(), seq.strip() )

    return fetch_func()


def is_model_exists( code: str ) -> bool :
    return False


def is_valid_sequence_fasta( data: SequenceFasta ) -> bool :
    code, _, sequence = data
    return 0 < len(code) and 0 < len(sequence)


async def modeller_protein_builder_closure( jobid: int, fetcher : AsyncGenerator[SequenceFasta,None] ) -> Coroutine[ None, None, list[int] ] :

    async def build_func() :
        results = [ await _build( fasta ) async for fasta in fetcher ]
        print( f"{jobid} : {results}" )
        return results

    async def _build( fasta: SequenceFasta) :
        code, _, seq = fasta
        print( f"{jobid:2d}: {code}" )
        ret = int( await process_command( FIBO_EXE + " " + str(42) ) )
        enc = await process_command( f"echo '{seq}' | shasum -a 512256 | shasum -a 512256 | shasum -a 512256" )
        print( f"{jobid:2d}: {code} {ret} {enc[:50]}" )
        return ret

    async def process_command( cmd: str ) -> str :
        proc = await asyncio.create_subprocess_shell(
                cmd,
                stderr=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE
            )
        stdout, _ = await proc.communicate()
        ret = stdout.decode("utf-8")
        return ret

    return build_func()


async def rosettafold_protein_builder_closure( jobid: int, fetcher : AsyncGenerator[SequenceFasta,None] ) -> Coroutine[ None, None, list[int] ] :
    async def build_func() :
        raise NotImplementedError()

    return build_func()


async def alphafold_protein_builder_closure( jobid: int, fetcher : AsyncGenerator[SequenceFasta,None] ) -> Coroutine[ None, None, list[int] ] :
    async def build_func() :
        raise NotImplementedError()

    return build_func()


async def main() -> None :
    MAX_WORKERS : int = multiprocessing.cpu_count()
    start = time.perf_counter()

    lock = asyncio.Lock()
    fetcher = await fasta_sequence_fetch_closure(FASTA_DATA, lock)
    builder = modeller_protein_builder_closure
    async with asyncio.TaskGroup() as tg:
        tasks = [ tg.create_task( await builder(id, fetcher) ) for id in range(MAX_WORKERS) ]
    results = [ task.result() for task in tasks ]

    print( [ r for rs in results for r in rs ] )
    print( f"Elapsed time {time.perf_counter() - start:.1f}" )


if __name__ == "__main__" :
    asyncio.run( main() )
