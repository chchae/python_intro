from .payment import Payment

class GooglePayPayment(Payment) :
    def pay( self, amount : float ) -> None :
        print( f"GooglePayPayment : pay ${amount}" )
    

