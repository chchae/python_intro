from src import prime

def test_prime() -> None :
    assert prime.is_prime(52756) is False
    assert prime.is_prime(52757) is True

def test_primes() -> None :
    assert len( prime.collect_primes(10240) ) == 1255

