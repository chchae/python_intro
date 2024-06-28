from .payment import Payment

class CreditCardPayment(Payment) :
    def pay( self, amount : float ) -> None :
        print( f"CreditCardPayment : pay ${amount}" )
    

