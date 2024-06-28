from email_builder import EMailBuilder



def main() -> None :
    email_message = (
        EMailBuilder()
            .set_from( "FROM@aaa.com" )
            .add_to( "TO@abc.com").add_to( "To@abc.com")
            .set_subject( "SUBJECT SUBJECT subject")
            .set_body( "BODY\nBODY\nBody\n")
            .build()
    )

    print( email_message )
    email_message.send()

if __name__ == "__main__" :
    main()
