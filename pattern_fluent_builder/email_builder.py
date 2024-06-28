from dataclasses import dataclass
from typing import Optional, Self
from email_message import EmailMessage


@dataclass
class EMailBuilder :
    _email_message = EmailMessage()

    def set_from( self, mfrom : str ) -> Self :
        self._email_message.mailfrom = mfrom
        return self

    def set_subject( self, _subject : str ) -> Self :
        self._email_message.subject = _subject
        return self

    def set_body( self, _body : str ) -> Self :
        self._email_message.body = _body
        return self

    def add_to( self, *mtos : list[str] ) -> Self :
        for mto in mtos :
            self._email_message.mailto.append( mto )
        return self

    def add_cc( self, *ccs : str ) -> Self :
        for cc in ccs :
            self._email_message.cc.append( cc )
        return self

    def add_bcc( self, *bccs : str ) -> Self :
        for bcc in bccs :
            self._email_message.bcc.append( bcc )
        return self

    def build(self) -> EmailMessage :
        return self._email_message
    

def main() -> None :
    emm = EmailMessage( "from@abc.com", ["to@abc.com",], "subject", "body\nbody\nbody" )
    emm.mailfrom = "FROM@abc.com"
    emm.mailto = [ "TO@abc.com", "TO@abc.com" ]
    print( emm )
    emm.send()

if __name__ == "__main__" :
    main()
