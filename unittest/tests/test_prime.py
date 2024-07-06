from src.prime import is_prime, collect_primes 

def test_prime() -> None :
    assert is_prime(52756) is False
    assert is_prime(52757) is True

def test_primes() -> None :
    assert len( collect_primes(10240) ) == 1255

