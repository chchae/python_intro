def is_prime( num : int ) -> bool :
    if num < 2 :
        return False
    for i in range( 2, num ) :
        if num % i == 0 :
            return False
    else:
        return True


print( is_prime(89))


def calculate_primes( start : int, finish: int ) -> list[int] :
    return [ n for n in range( start, finish ) if is_prime(n) ]

