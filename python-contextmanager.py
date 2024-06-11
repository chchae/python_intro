from contextlib import contextmanager
import random
from typing import Iterator



@contextmanager
def seed( a : int | float | str | bytes | bytearray | None = None ) -> Iterator[None] :
    try :
        random.seed(a)
        print( "Yielding" )
        yield
    finally :
        print( "Resetting seed" )
        random.seed()



def main() -> None :
    with seed( 42 ) :
        print( random.random() )
        print( random.random() )


if __name__ == "__main__" :
    main()
    