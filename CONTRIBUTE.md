# Setting up env

To set up local dev environment all you need to do is:
```shell
pyvenv env
. env/bin/activate
pip install -e requirements-dev.txt
```

To verify everything is installed correctly run tests:
```
py.test
```

# Running bot

Bot requires `TG_BOT_TOKEN` environment variable to be set.

However, if you do not want to register you own Telegram bot
there is a simple interactive terminal interface.
Just run the bot and it will fall back to std in/out instead of real Telegram API calls.

```shell
python tg_bot.py
```
