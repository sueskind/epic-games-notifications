# Epic Games Store free weekly games notifications

This is a short Python script for getting the current Epic Games Store weekly free offers via Telegram or Signal
messenger notifications.

<img src="img/tg.png" width="500">

## Prerequisites

- Python 3.6+
- [Functioning telegram bot](https://www.google.com/search?q=how+to+create+telegram+bot) **or**
- [Function signal bot](https://github.com/AsamK/signal-cli)

## Installation

```shell
pip install -r requirements.txt
```

## Usage

**Important! In order for a Telegram bot to send a message, it must be allowed to do that first: Send `/start` to the
bot.**

### Basic usage

```python
from src.notifier import Notifier

# Create notifier with telegram token
notifier = Notifier(service=Notifier.TELEGRAM, bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ", country="DE")
# or with signal number
notifier = Notifier(service=Notifier.SIGNAL, signal_sender_number="+123456789", country="DE")

# Get current/upcoming offers from Epic Games Store
notifier.update_offers()

# Send notifications to a list of Telegram chat ids.
notifier.notify(recipients=[123456])
# or phone numbers for Signal
notifier.notify(recipients=["+123456789"])
```

### Repeating notifications

```python
# Send weekly notifications at certain day of week at certain time.
notifier.notify_weekly([123456], 4, "17:48", show_days=True, ignore_errors=True)

# ... or ...

# Send notifications when a change was detected
notifier.notify_on_change([123456, 567890], 300, initial=True, show_days=False, ignore_errors=True)
```

For further explanation look at the docstrings of the functions.

## FAQ

**How do I find out a/my chat id?**  
Send a message to your bot. Then go to `https://api.telegram.org/bot<TOKEN>/getUpdates`. It should show recent messages
together with the chat id of the sender.