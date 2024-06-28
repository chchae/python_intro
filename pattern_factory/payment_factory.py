from inspect import getmembers, isclass, isabstract
import payment_methods
from payment_methods import Payment



class PaymentFactory(object) :
    payment_implementations : dict[str, Payment] = {}

    def __init__( self ) :
        self.load_payment_methods()

    def load_payment_methods(self) -> None :
        implementations = getmembers( payment_methods, lambda m: isclass(m) and not isabstract(m) )
        for name, _type in implementations:
            if isclass(_type) and issubclass(_type, Payment) :
                self.payment_implementations[name] = _type

    def create( self, payment_type : str ) -> Payment :
        if payment_type in self.payment_implementations :
            return self.payment_implementations[payment_type]()
        else:
            raise ValueError( f"Unknown payment method : {payment_type = }" )
