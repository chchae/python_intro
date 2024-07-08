from typing import Callable
from functools import partial, reduce


def quick_sort[T]( data: list[T] ) -> list[T] :
    if len(data) <= 1 :
        return data.copy()
    pivot = data[ len(data) // 2 ]
    left = [x for x in data if x > pivot ]
    middle = [x for x in data if x == pivot ]
    right = [x for x in data if x < pivot ]
    return quick_sort(left) + middle + quick_sort(right)

def quick_sort[T]( data: list[T] ) -> list[T] :
    match data:
        case [] | [_] :
            return data.copy()
        case [pivot, *rest] :
            left = [x for x in data if x < pivot ]
            middle = [x for x in data if x == pivot ]
            right = [x for x in data if x > pivot ]
            return quick_sort(left) + middle + quick_sort(right)


def multiply_x[T]( data: list[T], x: T ) -> list[T] :
    return list( map( lambda y: y * x, data ) )

def add_x[T]( data: list[T], x: T ) -> list[T] :
    return list( map( lambda y: y + x, data ) )



type Composable[T] = Callable[ [T], T ]

def compose( *functions: Composable ) -> Composable :
    def inner(arg) :
        result = arg
        for fn in functions:
            result = fn(result)
        return result
    return inner


def compose[T]( *functions: Composable ) -> Composable :
    def apply( value: T, fn: Composable[T] ) -> T :
        return fn(value)
    return lambda data: reduce( apply, functions, data )    


multiply_2 = partial( multiply_x, x=2 )
add_10 = partial( add_x, x=10 )

do_operations = compose( multiply_2, add_10, quick_sort )

data = [ 1, 5, 3, 4, 2 ]
print( do_operations( data ) )
