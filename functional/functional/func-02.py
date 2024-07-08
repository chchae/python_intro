from functools import cache, partial, wraps



def with_greeting( func ) :
    @wraps(func)
    def wrapper( *args, **kwargs ) :
        print( "hello world!" )
        return func(*args, **kwargs)
    return wrapper

@with_greeting
def add(x, y):
    return x + y 


print( add( 1, 2 ) )
print( add.__name__, add.__doc__ )
