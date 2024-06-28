from abc import ABC, abstractmethod

class Payment(ABC) :
    @abstractmethod
    def pay( self, amount : float ) -> None :
        raise NotImplementedError( "Payment method not implemented" )
    