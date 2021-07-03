from src.notifier import Notifier

if __name__ == '__main__':
    n = Notifier(service=Notifier.TELEGRAM, telegram_bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ", country="DE")
    n.update_offers()
    n.notify(recipients=[123456])

    n = Notifier(service=Notifier.SIGNAL, signal_sender_number="+123456789", country="DE")
    n.update_offers()
    n.notify(recipients=["+123987654"])
