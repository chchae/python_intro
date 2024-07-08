from typing import Generic, Optional, Literal

# T = TypeVar( 'T' )
# class Stack[T] :
# class Stack(Generic(T)) :
class Stack[T] :
    def __init__( self ) -> None :
        self._container : list[T] = []

    def __str_( self ) -> str :
        return str( self._container )

    def push( self, item : T ) -> None :
        self._container.append( item )

    def pop( self ) -> T :
        return self._container.pop()

    def peek( self ) -> Optional[T] :
        if self.is_empty() :
            return None
        return self._container[-1]



class NumericStack[ T : ( int, float ) ]( Stack[T] ) :
    def __getitem__( self, index : int ) -> T :
        return self._container[index]

    def __setitem__( self, index : int, value : T ) -> None :
        if 0 <= index < len( self._container ) :
            self._container[index] = value
        else :
            raise IndexError( f"stack index out of range {index} / {len( self._container )}" )

    def sum( self ) -> T | Literal[0] :
    # def sum( self ) -> T  :
        return sum( self._container )

    def average( self ) -> float :
        if self.is_empty() :
            return 0
        total : T | Literal[0] = self.sum()
        return total / self.size()

    def max(self) -> T | None :
        if self.is_empty() :
            return None
        return max( self._container )

    def min(self) -> T | None :
        if self.is_empty() :
            return None
        return min( self._container )



def main() -> None :
    ns = NumericStack[int]()
    for i in range(5) :
        ns.push(i )
    print( ns )


if __name__ == "__main__" :
    main()
