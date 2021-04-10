# Epic Games Store free weekly games notifications

This is a short Python script for getting the current Epic Games Store weekly free offers via Telegram notifications.

## Prerequisites

- Python 3.6+
- [Functioning telegram bot](https://www.google.com/search?q=how+to+create+telegram+bot)

## Installation

```shell
pip install -r requirements.txt
```

## Usage

```python
# Create notifier with telegram token
notifier = Notifier(bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ", country="DE")

# Get current/upcoming offers from Epic Games Store
notifier.update_offers()

# Send notifications to a list of telegram chat ids.
notifier.notify(chat_ids=[123456])
```

**Important! In order for a Telegram bot to send a message, it must be allowed to do that first: Send `/start` to the
bot.**

