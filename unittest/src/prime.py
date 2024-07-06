def is_prime( num : int ) -> bool:
    if num < 2 :
        return False
    for i in range( 2, num // 2 ) :
        if num % i == 0 :
            return False
    return True


def collect_primes( top : int ) -> list[int] :
    return [ n for n in range(top) if is_prime(n) ]
