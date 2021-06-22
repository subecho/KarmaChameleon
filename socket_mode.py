import os
import re

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ["SLACK_BOT_TOKEN"])


@app.message(re.compile(r".*\+\+$"))
def do_increment(message, say):
    text_elem = message["text"]
    item = text_elem.split("++")[0]
    say(f"woo, {item} got incremented!")


@app.message(re.compile(r".*--$"))
def do_decrement(message, say):
    item = message["text"].split("--")[0]
    say(f"aww, {item} got decremented :(")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
