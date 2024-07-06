from src import fibo 

def test_fibonacci() -> None :
    assert 9227465 == fibo.fibonacci(34)
