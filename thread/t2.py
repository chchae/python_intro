import random
from dataclasses import dataclass
from itertools import groupby
from functools import partial
from typing import Generator
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor, as_completed, Future



def is_model_exists( code: str ) -> bool :
    return False


def fetcher_dummy(_: int | str | None = None) -> Generator[str, None, None] :
    _seqs : list[int] = [ random.randint( 35, 42 ) for _ in range(100) ]
    for id in _seqs:
        yield str(id)




@dataclass
class SequenceFasta:
    code : str = ""
    descr : str = ""
    sequence : str = ""

    def is_valid(self) -> bool :
        return 0 < len(self.code) and 0 < len(self.sequence)

def split_titleline( line: str ) -> tuple[str, str] :
    (code, descr) = line[1:].split( '|', 1 )
    return code.strip(), descr.strip()

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

    print( f"{jobid} : {seq = }")
    # cmd = "python /Users/chchae/bin/rsa-encode.py " + seq
    cmd = f"echo '{seq}' | shasum -a 512256 | shasum -a 512256"
    ret = subprocess.check_output( cmd, shell=True ).decode("utf-8").strip()
    print( f"{jobid} : {seq = }, {ret =}")
    return jobid





def main() -> None :
    MAX_WORKERS : int = cpu_count()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        fname = "/Users/chchae/work/data/sequence-short.fasta"
        fetch_func = partial( fetcher_fasta, filename=fname )
        build_func = partial( build_fasta )
        futures : list[Future[int]] = []
        for id, seq in enumerate( fetch_func() ) :
            #print( id, seq.code, seq.descr )
            if is_model_exists( seq.code ) :
                continue
            futures.append( executor.submit( build_func, seq.sequence, id ) ) 
        results = [ future.result() for future in as_completed(futures) ]
        print(results)
    print( f"Done {len(results)}-sequences...")

if __name__ == "__main__" :
    main()
