# closure version :
#

import sys
import random
from itertools import groupby
from typing import Generator, Callable
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor

if sys.platform == "darwin":
    FASTA_DATA = "/Users/chchae/work/data/sequence-short.fasta"
    FIBO_EXE = "/Users/chchae/bin/fibo "
else:
    FASTA_DATA = "/home/chchae/work/data/sequence-short.fasta"
    FIBO_EXE =  "/home/chchae/bin/fibo "


SequenceFasta = tuple[ str, str, str ]
SequenceGenerator = Generator[SequenceFasta, None, None]
SequenceFetcherFuncType = Callable[ [], SequenceGenerator ]
BuilderFuncType = Callable[ [SequenceFasta], int ]


def is_model_exists( code: str ) -> bool :
    return False


def is_valid_sequence_fasta( data: SequenceFasta ) -> bool :
    code, _, sequence = data
    return 0 < len(code) and 0 < len(sequence)


def dummy_sequence_fetch_closure( length: int = 128, count: int = 100 ) -> SequenceFetcherFuncType :
    _seqs : list[str] = [
        ''.join( random.choices( "ACDEFGHIKLMPQRSTVWY", k=length ) ) for _ in range(count)
    ]

    def fetch_func() -> SequenceGenerator :
        for id in _seqs:
            yield (id, id, id)

    return fetch_func


def fasta_sequence_fetch_closure( filename : str ) -> SequenceFetcherFuncType :
    def fetch_func() -> SequenceGenerator :
        with open( filename ) as ifp :
            lines = ( x[1] for x in groupby(ifp, lambda line: str(line).startswith(">") ) )
            for header in lines:
                headerStr = str(header.__next__())
                (name, descr) = headerStr[1:].strip().split( '|', 1 )
                seq = "".join( s.strip() for s in lines.__next__() )
                yield ( name.strip(), descr.strip(), seq.strip() )

    return fetch_func


def oracle_sequence_fetcher_closure( url : str, userid : str, passwd : str ) -> SequenceFetcherFuncType :
    def fetch_func() -> SequenceGenerator :
        raise NotImplementedError()
    
    return fetch_func


def dummy_protein_builder_closure( jobid : int ) :
    def build_func( data : SequenceFasta ) -> int :
        import subprocess
        nseed = random.randint( 35, 42)
        print( f"{jobid = :2d}, {nseed = :2d}" )
        cmd = FIBO_EXE + str(nseed)
        ret = subprocess.check_output( cmd, shell=True ).decode("utf-8")
        print( f"{jobid = :2d}, {nseed = :2d}, {ret = }" )
        return int(ret)
    
    return build_func


def modeller_protein_builder_closure( jobid : int = 0 ) -> BuilderFuncType :
    def build_func( data : SequenceFasta ) -> int :
        code, _, seq = data
        ret = _build_1(seq)
        print( f"{code}: {seq[:20]} {ret[:46]}")
        res = _build_2(code)
        return res
    
    def _build_1( seq: str ) -> str :
        import subprocess
        cmd = f"echo '{seq}' | shasum -a 512256 | shasum -a 512256 | shasum -a 512256"
        return subprocess.check_output( cmd, shell=True ).decode("utf-8").strip()

    def _build_2( code: str ) -> int :
        import subprocess
        nseed = random.randint( 39, 42)
        print( f"{code} : {nseed = :2d}" )
        cmd = FIBO_EXE + str(nseed)
        ret = subprocess.check_output( cmd, shell=True ).decode("utf-8")
        print( f"{code} : {nseed = :2d}, {ret = }" )
        return int(ret)

    return build_func


def rosettafold_protein_builder_closure( jobid : int = 0 ) -> BuilderFuncType :
    def build_func( data : SequenceFasta ) -> int :
        raise NotImplementedError()

    return build_func


def alphafold_protein_builder_closure( jobid : int = 0 ) -> BuilderFuncType :
    def build_func( data : SequenceFasta ) -> int :
        raise NotImplementedError()

    return build_func


def get_sequences() -> SequenceGenerator :
    fetcher = fasta_sequence_fetch_closure(FASTA_DATA)
    sequences : SequenceGenerator = ( s for s in fetcher() )
    return sequences


def main() -> None :
    MAX_WORKERS : int = cpu_count()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        sequences = get_sequences()
        builder = modeller_protein_builder_closure()
        results = executor.map( builder, sequences )
        # print( list(results) )
    print( f"Done {len(list(results))}-sequences...")


if __name__ == "__main__" :
    main()
