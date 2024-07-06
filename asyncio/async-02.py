from dataclasses import dataclass
from typing import Generator
import rsa


@dataclass
class SequenceFasta:
    code : str = ""
    descr : str = ""
    sequence : str = ""

    def is_valid(self) -> bool :
        return 0 < len(self.code) and 0 < len(self.sequence)


def db_insert( cursor: str, data: SequenceFasta ) -> None :
    # print( f"INSERT: [{data.code}] [{data.descr}] [{data.sequence}]" )
    publicKey, _ = rsa.newkeys(2048)
    msg = data.sequence[:200]
    enc = rsa.encrypt(msg.encode(), publicKey)
    print("encrypted string: ", enc)


@dataclass
class FastaReader:
    filename : str = ""

    def read(self) -> Generator[ SequenceFasta, None, None] :
        with open( fname ) as ifp :
            code : str = ""
            descr : str = ""
            seq : str = ""
            for line in ifp.readlines() :
                if not line.startswith( '>' ) :
                    seq += line.strip()
                    continue

                # end of sequence at previous line
                yield SequenceFasta(code, descr, seq)

                # start of new sequence from this line
                (code, descr) = FastaReader._split_titleline( line )
                seq = ""
            
            else :  # EOF
                #print( f"LAST SEQ: {code}, {descr}" )
                yield SequenceFasta(code, descr, seq)

    @staticmethod
    def _split_titleline( line: str ) -> tuple[str, str] :
        (code, descr) = ( line[1:] ).split( '|', 1 )
        return code.strip(), descr.strip()


def main( fname: str ) -> None :
    num_seq : int = 0
    for data in FastaReader( fname ).read() :
        if not data.is_valid() :
            continue
        print( f"{data.code} :  {data.sequence}\n" )
        db_insert( "", data )
        num_seq += 1
        #if 3 < num_seq :
        #    break
    print( f"\nDone {num_seq}-sequences...")


if __name__ == "__main__" :
    fname = "/Users/chchae/work/data/seq.fasta"
    main( fname )

