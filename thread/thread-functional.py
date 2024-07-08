import os
import random
from dataclasses import dataclass
from itertools import groupby
from typing import Generator, Callable
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

if os.name == "posix":
    FASTA_DATA = "/home/chchae/work/data/sequence-short.fasta"
    FIBO_EXE =  "/home/chchae/bin/fibo "
else:
    FASTA_DATA = "/Users/chchae/work/data/sequence-short.fasta"
    FIBO_EXE = "/Users/chchae/bin/fibo "


SequenceFasta = tuple[ str, str, str ]
SequenceFetcherFunc = Callable[ [], SequenceFasta ]


def is_model_exists( code: str ) -> bool :
    return False


def is_valid_sequence_fasta( data: SequenceFasta ) -> bool :
    return 0 < len(data.code) and 0 < len(data.sequence)


def dummy_sequence_fetch_closure( length: int = 128, count: int = 100 ) -> SequenceFetcherFunc :
    _seqs : list[str] = [
        ''.join( random.choices( "ACDEFGHIKLMPQRSTVWY", k=length ) ) 
        for _ in range(count)
    ]

    def fetch_func(self) -> Generator[SequenceFasta, None, None] :
        for id in _seqs:
            yield SequenceFasta(str(id), str(id), str(id))

    return fetch_func


def fasta_sequence_fetch_closure( filename : str ) :
    def fetch_func() -> Generator[SequenceFasta, None, None] :
        with open( filename ) as ifp :
            lines = ( x[1] for x in groupby(ifp, lambda line: str(line).startswith(">") ) )
            for header in lines:
                headerStr = str(header.__next__())
                (name, descr) = headerStr[1:].strip().split( '|', 1 )
                seq = "".join(s.strip() for s in lines.__next__())
                yield (name, descr, seq)

    return fetch_func


def oracle_sequence_fetcher_closure( url : str, userid : str, passwd : str ) :
    def fetch_func(self) -> Generator[SequenceFasta, None, None] :
        raise NotImplementedError()
    
    return fetch_func


def dummy_protein_builder_closure( jobid : int ) :
    def build_func( data : SequenceFasta ) -> int :
        import subprocess
        nseed = random.randint( 35, 42)
        print( f"start  : {jobid = :2d}, {nseed = :2d}" )
        cmd = FIBO_EXE + str(nseed)
        ret = subprocess.check_output( cmd, shell=True ).decode("utf-8")
        print( f"finish : {jobid = :2d}, {nseed = :2d}, {ret = }" )
        return int(ret)
    
    return build_func


def modeller_protein_builder_closure( jobid : int ) :
    def build_func( data : SequenceFasta ) -> int :
        _, _, seq = data
        res = _build_1(seq)
        res += _build_2(seq)
        return res
    
    def _build_1( seq: str ) -> int :
        import subprocess
        cmd = f"echo '{seq}' | shasum -a 512256 | shasum -a 512256 | shasum -a 512256"
        ret = subprocess.check_output( cmd, shell=True ).decode("utf-8").strip()
        print( f"{jobid}: {seq[:20]} {ret[:56]}")
        return jobid

    def _build_2( seq: str ) -> int :
        import subprocess
        nseed = random.randint( 39, 42)
        print( f"start  : {jobid = :2d}, {nseed = :2d}" )
        cmd = FIBO_EXE + str(nseed)
        ret = subprocess.check_output( cmd, shell=True ).decode("utf-8")
        print( f"finish : {jobid = :2d}, {nseed = :2d}, {ret = }" )
        return int(ret)

    return build_func


def rosettafold_protein_builder_closure( jobid : int ) :
    def build_func( data : SequenceFasta ) -> int :
        raise NotImplementedError()

    return build_func


def alphafold_protein_builder_closure( jobid : int ) :
    def build_func( data : SequenceFasta ) -> int :
        raise NotImplementedError()

    return build_func



def main() -> None :
    MAX_WORKERS : int = cpu_count()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        fname = FASTA_DATA
        fetcher = fasta_sequence_fetch_closure(fname)
        futures : list[Future[int]] = []
        for id, seq in enumerate( fetcher(), 1 ) :
            if is_model_exists( seq[0] ) :
                continue
            builder = modeller_protein_builder_closure(id)
            futures.append( executor.submit( builder, seq ) )
            if id > 100 :
                break 
        results = [ future.result() for future in as_completed(futures) ]
        # print(results)
    print( f"Done {len(results)}-sequences...")


if __name__ == "__main__" :
    main()
