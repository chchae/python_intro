from src.fibo  import fibonacci

def test_fibonacci() -> None :
    assert 9227465 == fibonacci(34)
    