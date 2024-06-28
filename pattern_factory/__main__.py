from payment_factory import PaymentFactory


def main() -> None :
    factory = PaymentFactory()
    payment = factory.create( "GooglePayPayment" )
    payment.pay( amount=100.0 )


if __name__ == "__main__" :
    main()
