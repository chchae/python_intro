import random
from dataclasses import dataclass
from abc import ABC, abstractmethod
from itertools import groupby
from functools import partial
from typing import Generator
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor, as_completed, Future



def is_model_exists( code: str ) -> bool :
    return False


@dataclass
class SequenceFasta:
    code : str = ""
    descr : str = ""
    sequence : str = ""

    def is_valid(self) -> bool :
        return 0 < len(self.code) and 0 < len(self.sequence)



def fetcher_dummy(_: int | str | None = None) -> Generator[str, None, None] :
    _seqs : list[int] = [ random.randint( 35, 42 ) for _ in range(100) ]
    for id in _seqs:
        yield str(id)

def fetcher_fasta( filename : str ) -> Generator[SequenceFasta, None, None] :
    with open( filename ) as ifp :
        lines = ( x[1] for x in groupby(ifp, lambda line: str(line).startswith(">") ) )
        for header in lines:
            headerStr = str(header.__next__())
            (name, descr) = headerStr[1:].strip().split( '|', 1 )
            seq = "".join(s.strip() for s in lines.__next__())
            yield SequenceFasta(name, descr, seq)


def build_dummy( seq: str, jobid: int = 0 ) -> int :
    import subprocess
    nseed = int(seq)
    cmd = "/Users/chchae/bin/fibo " + str(nseed)
    print( f"{jobid} : {nseed = }")
    ret = subprocess.check_output( cmd, shell=True ).decode("utf-8")
    print( f"{jobid} : {nseed = }, {ret =}")
    return int(ret)

def encode_rsa( msg : str ) -> bytes :
    import rsa
    publicKey, _ = rsa.newkeys(2048)
    return rsa.encrypt(msg.encode(), publicKey)

def build_fasta( seq: str, jobid: int = 0 ) -> int :
    import subprocess

    #print( f"{jobid} : {seq = }")
    # cmd = "python /Users/chchae/bin/rsa-encode.py " + seq
    cmd = f"echo '{seq}' | shasum -a 512256 | shasum -a 512256 | shasum -a 512256 | shasum -a 512256"
    ret = subprocess.check_output( cmd, shell=True ).decode("utf-8").strip()
    print( f"{jobid} : {seq = }, {ret =}")
    return jobid


def main_functions() -> None :
    MAX_WORKERS : int = cpu_count()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        fname = "/Users/chchae/work/data/sequence-short.fasta"
        fetch_func = partial( fetcher_fasta, filename=fname )
        build_func = partial( build_fasta )
        futures : list[Future[int]] = []
        for id, seq in enumerate( fetch_func() ) :
            if is_model_exists( seq.code ) :
                continue
            futures.append( executor.submit( build_func, seq.sequence, id ) ) 
        results = [ future.result() for future in as_completed(futures) ]
        # print(results)
    print( f"Done {len(results)}-sequences...")









class SequenceFetcher(ABC) :
    @abstractmethod
    def fetch(self) -> Generator[SequenceFasta, None, None] :
        raise NotImplementedError()


class DummySequenceFetcher(SequenceFetcher) :
    def __init__(self, length:int = 128, count : int = 100 ) :
        self._seqs : list[str] = [
            ''.join( random.choices( "ACDEFGHIKLMPQRSTVWY", k=length ) ) 
            for _ in range(count)
        ]

    def fetch(self) -> Generator[SequenceFasta, None, None] :
        for id in self._seqs:
            yield SequenceFasta(str(id), str(id), str(id))


@dataclass
class FastaSequenceFetcher(SequenceFetcher) :
    _filename : str = ""

    def fetch(self) -> Generator[SequenceFasta, None, None] :
        with open( self._filename ) as ifp :
            lines = ( x[1] for x in groupby(ifp, lambda line: str(line).startswith(">") ) )
            for header in lines:
                headerStr = str(header.__next__())
                (name, descr) = headerStr[1:].strip().split( '|', 1 )
                seq = "".join(s.strip() for s in lines.__next__())
                yield SequenceFasta(name, descr, seq)


class OracleSequenceFetcher(SequenceFetcher) :
    url : str = ""
    userid : str = ""
    passwd : str = ""
    def fetch(self) -> Generator[SequenceFasta, None, None] :
        raise NotImplementedError()



@dataclass
class ProteinBuilder(ABC) :
    jobid : int = 0

    @abstractmethod
    def build( self, seq: str, jobid: int = 0 ) -> int :
        raise NotImplementedError()


@dataclass
class DummyProteinBuilder(ProteinBuilder) :
    def build( self, seq: str, jobid: int = 0 ) -> int :
        import subprocess
        nseed = random.randint( 35, 42)
        print( f"start  : {self.jobid = :2d}, {nseed = :2d}" )
        cmd = "/Users/chchae/bin/fibo " + str(nseed)
        ret = subprocess.check_output( cmd, shell=True ).decode("utf-8")
        print( f"finish : {self.jobid = :2d}, {nseed = :2d}, {ret = }" )
        return int(ret)

class ModellerProteinBuilder(ProteinBuilder) :
    def build( self, seq: str, jobid: int = 0 ) -> int :
        import subprocess

        cmd = f"echo '{seq}' | shasum -a 512256 | shasum -a 512256"
        ret = subprocess.check_output( cmd, shell=True ).decode("utf-8").strip()
        print( f"{jobid} : {seq[:10]} {ret}")
        return jobid

class RosettaFoldProteinBuilder(ProteinBuilder) :
    def build( self, seq: str, jobid: int = 0 ) -> int :
        raise NotImplementedError()

class AlphaFoldProteinBuilder(ProteinBuilder) :
    def build( self, seq: str, jobid: int = 0 ) -> int :
        raise NotImplementedError()



def main() -> None :
    MAX_WORKERS : int = cpu_count()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # fetcher = DummySequenceFetcher(128, 300)
        # builder = DummyProteinBuilder(0)
        fname = "/Users/chchae/work/data/sequence-short.fasta"
        fetcher = FastaSequenceFetcher(fname)
        builder = ModellerProteinBuilder(0)
        futures : list[Future[int]] = []
        for id, seq in enumerate( fetcher.fetch() ) :
            if is_model_exists( seq.code ) :
                continue
            futures.append( executor.submit( builder.build, seq.sequence, id ) ) 
        results = [ future.result() for future in as_completed(futures) ]
        # print(results)
    print( f"Done {len(results)}-sequences...")


if __name__ == "__main__" :
    # main_functions()
    main()
