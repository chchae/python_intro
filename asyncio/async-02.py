from dataclasses import dataclass
from typing import Generator
from itertools import groupby


@dataclass
class SequenceFasta:
    code : str = ""
    descr : str = ""
    sequence : str = ""

    def is_valid(self) -> bool :
        return 0 < len(self.code) and 0 < len(self.sequence)


def encode_rsa( msg : str ) -> bytes :
    import rsa
    publicKey, _ = rsa.newkeys(2048)
    return rsa.encrypt(msg.encode(), publicKey)


def db_insert( cursor: str, data: SequenceFasta ) -> None :
    print( f"INSERT: [{data.code}] [{data.descr}] [{data.sequence}]\n" )
    if False :
        print("encrypted string: ", encode_rsa( data.sequence[:200] ) )


@dataclass
class FastaReader:
    filename : str = ""

    def read_binary(self) -> Generator[ SequenceFasta, None, None] :
        with open( self.filename, 'rb' ) as ifp :
            lines = ( x[1] for x in groupby(ifp, lambda line: str(line, 'utf-8').startswith(">") ) )
            for header in lines:
                headerStr = str(header.__next__(), 'utf-8')
                (name, descr) = headerStr[1:].strip().split( '|', 1 )
                seq = "".join(str(s, 'utf-8').strip() for s in lines.__next__())
                yield SequenceFasta(name, descr, seq)

    def read(self) -> Generator[ SequenceFasta, None, None] :
        with open( self.filename ) as ifp :
            lines = ( x[1] for x in groupby(ifp, lambda line: str(line).startswith(">") ) )
            for header in lines:
                headerStr = str(header.__next__())
                (name, descr) = headerStr[1:].strip().split( '|', 1 )
                seq = "".join(s.strip() for s in lines.__next__())
                yield SequenceFasta(name, descr, seq)

    @staticmethod
    def _split_titleline( line: str ) -> tuple[str, str] :
        (code, descr) = line[1:].split( '|', 1 )
        return code.strip(), descr.strip()


def main( fname: str ) -> None :
    num_seq : int = 0
    for data in FastaReader( fname ).read() :
        if data.is_valid() :
            db_insert( "", data )
            num_seq += 1
            #if 3 < num_seq :
            #    break
        else :
            raise ValueError( "\n!!! Invalid sequence data {data.code}, {data.sequence}")
    print( f"\nDone {num_seq}-sequences...")


if __name__ == "__main__" :
    fname = "/Users/chchae/work/data/sequence-short.fasta"
    main( fname )

