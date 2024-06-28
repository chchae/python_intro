from dataclasses import dataclass
from typing import Optional


@dataclass
class EmailMessage :
    _mailfrom : str = ""
    _mailto : list[str] = None
    _subject : str  = ""
    _body : str = ""
    _cc : Optional[ list[str] ] = None
    _bcc : Optional[ list[str]] = None
    _attachment : Optional[ list[str] ] = None


    @property
    def mailfrom( self) -> str :
        return self._mailfrom

    @property
    def subject( self) -> str :
        return self._subject

    @property
    def body( self) -> str :
        return self._body

    @property
    def mailto( self) -> list[str] :
        if None is self._mailto :
            self._mailto = []
        return self._mailto

    @property
    def cc( self) -> list[str] :
        if None is self._cc :
            self._cc = []
        return self._cc

    @property
    def bcc( self) -> list[str] :
        if None is self._bcc :
            self._bcc = []
        return self._bcc

    @mailfrom.setter
    def mailfrom( self, _mailfrom : str ) -> None :
        self._mailfrom = _mailfrom

    @subject.setter
    def subject( self, _subject : str ) -> None :
        self._subject = _subject

    @body.setter
    def body( self, _body : str ) -> None :
        self._body = _body

    @mailto.setter
    def mailto( self, _mailto : list[str] ) -> None :
        self._mailto = _mailto.copy()
    
    # @overload  <- function overloading
    @mailto.setter
    def mailto( self, _mailto : str ) -> None :
        if None is self._cc :
            self._cc = []
        self._mailto.append( _mailto )

    @cc.setter
    def cc( self, _cc : list[str] ) -> None :
        self._cc = _cc.copy()

    @cc.setter
    def cc( self, _cc : str ) -> None :
        if None is self._cc :
            self._cc = []
        self._cc.append( _cc )

    @bcc.setter
    def bcc( self, _bcc : list[str] ) -> None :
        self._bcc = _bcc.copy()

    @bcc.setter
    def bcc( self, _bcc : str ) -> None :
        if None is self._cc :
            self._cc = []
        self._bcc.append( _bcc )

    def send( self ) -> None :
        print( "Email successfully sent" )
        print( "-----------------------------------")
        print ( f"From : {self._mailfrom}" )
        print ( f"To : {self._mailto}" )
        print ( f"CC : {self._cc}" )
        print ( f"BCC : {self._bcc}" )
        print ( f"Body : {self._body}" )
        print ( f"Attachment : {self._attachment}" )
        print( "-----------------------------------")





def main() -> None :
    emm = EmailMessage( "from@abc.com", ["to@abc.com",], "subject", "body\nbody\nbody" )
    emm.mailfrom = "FROM@abc.com"
    emm.mailto = [ "TO@abc.com", "To@abc.com" ]
    emm.mailto = "to@abc.com"
    emm.cc = "CC@abc.com"
    print( emm )
    emm.send()

if __name__ == "__main__" :
    main()
