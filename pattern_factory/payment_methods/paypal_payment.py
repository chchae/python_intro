from .payment import Payment

class PayPalPayment(Payment) :
    def pay( self, amount : float ) -> None :
        print( f"PayPalPayment : pay ${amount}" )
    

