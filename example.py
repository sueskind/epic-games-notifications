from src.telegram import Notifier

if __name__ == '__main__':
    n = Notifier(bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ", country="DE")
    n.update_offers()
    n.notify(chat_ids=[123456])
