# Karma Chameleon Copyright (C) 2021 Dustin Schoenbrun, Will Rideout, Ben Decato
#
# This program is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this
# program. If not, see <http://www.gnu.org/licenses/>.

"""
KarmaChameleon

A simple Slack bot which allows users to assign karma to each other or things via the use
of "++" and "--" in messages.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Callable, Union
from slack_bolt import Ack, BoltResponse, Say

from karma_chameleon.bot import KarmaBot

# There is only one logger, with three different sub-loggers.  All loggers use the same
# file destination, and line format.  The logger with UID "karma_chameleon" is used to log
# events for the main app, i.e. the Flask app.  karma_chameleon.event_manager logs events
# and debug info pertaining to the event_manager.py methods.  karma_chameleon.bot logs
# events and debug info pertaining to the methods of the KarmaBot class.
#
# If the logs dir does not exit, make it.
if not os.path.exists("logs"):
    os.makedirs("logs")

# Create the "main" logger.  This logger has the file destination and line format that is
# inherited by all sub-loggers.
logger = logging.getLogger("karma_chameleon")
logger.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler(
    "logs/karma_chameleon.log", maxBytes=10_000_000, backupCount=3
)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s %(name)s %(levelname)s[%(funcName)s]: %(message)s"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

app = KarmaBot(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


@app.middleware
def log_message(
    body: dict, next: Callable  # pylint: disable=redefined-builtin
) -> Union[Callable, BoltResponse]:  # pylint: disable=unsubscriptable-object
    logger.debug("Received message: %s" % str(body))
    return next()


@app.middleware
def handle_no_karma_op(
    body: dict, next: Callable  # pylint: disable=redefined-builtin
) -> Union[Callable, BoltResponse]:  # pylint: disable=unsubscriptable-object
    """Middleware which enables KarmaChameleon to immediately and gracefully handle events
    which do not contain any karma operations or slash-commands.

    Unfortunately the Slack Bolt API requires that the next middleware method be referred
    to as "next", which is a built-in.  You can't win them all I suppose...

    Arguments:
    body -- a dict containing the entire Slack Bolt API event
    next -- callable reference to the next middleware listener.

    Returns:
    If the incoming event contains a karma operation, then the next middleware listener
    is returned and invoked by the caller of this middleware.  If there is no karma
    operation contained in the event, and the event is not a command, then a
    BoltResponse(200) is returned as we have nothing further to do.
    """
    if body.get("command"):
        return next()

    if body["event"]["type"] == "message" and "text" in body["event"]:
        msg = body["event"]["text"]
        if app.inc_regex.match(msg) or app.dec_regex.match(msg):
            return next()
    # This is too chatty to be left enabled, but it may be useful for debug in the future.
    # logger.debug("Ignoring event with no karma operation")
    return BoltResponse(status=200, body="Ignoring event with no karma operation")


@app.command("/k")
def handle_karma_command(ack: Ack, say: Say, command: dict) -> None:
    """Trigger a karma event, either increment or decrement.  The format of the command is
    as follows:

        /k SUBJECT (++|--) trailing_garbage

    The type of the karma event is determined by the use of "++" or "--" as indicated in
    the above syntax.  Trailing garbage is any explanation or other flavor text the user
    may provide in order to justify their awarding of karma, but it does nothing for this
    bot so it is ignored.  The SUBJECT of a karma event may be either a username via the
    "@" syntax of Slack, or an object.  Objects may be formatted as hashtags, but it
    doesn't matter as the symbol is stripped anyway.

    Arguments:
    ack -- acknowledgement method, called to acknowledge the command was received
    say -- method for printing back to the same channel from which the command was run
    command -- dictionary specifying the command, including any text which was pased
    """
    ack()
    event_type = command["text"].split()[1]
    uid = command["user_id"]

    msg = {
        "text": command["text"],
        "user": uid,
    }

    if event_type == "++":
        say(hdr_text + app.increment_karma(msg), user=uid)
    elif event_type == "--":
        say(hdr_text + app.decrement_karma(msg), user=uid)
    else:
        say("Hmmm... this doesn't look right.  Syntx is '/k SUBJECT (++|--) [FLAVOR]")


@app.message(app.inc_regex)
def increment(message: dict, say: Say) -> None:
    """Passes the message along for to the KarmaChameleon bot, then posts a response based
    on the return value of the bot's increment method.

    Arguments:
    message -- dictionary representation of the message which contains a karma operation
    say -- method for printing back to the same channel from which the command was run
    """
    rsp = app.increment_karma(message)
    say(rsp)


@app.message(app.dec_regex)
def decrement(message: dict, say: Say) -> None:
    """Passes the message along for to the KarmaChameleon bot, then posts a response based
    on the return value of the bot's decrement method.

    Arguments:
    message -- dictionary representation of the message which contains a karma operation
    say -- method for printing back to the same channel from which the command was run
    """
    rsp = app.decrement_karma(message)
    say(rsp)


@app.command("/leaderboard")
def show_leaderboard(ack: Ack, say: Say) -> None:
    """Invoke leaderboard display from the karmaChameleon bot.

    Arguments:
    ack -- acknowledgement method, called to acknowledge the command was received
    say -- method for printing back to the same channel from which the command was run
    """
    # Must acknowledge the command was run.
    ack()
    msg, users, things = app.display_karma_leaderboards()
    if msg:
        say(msg)
    if users:
        say(users)
    if things:
        say(things)


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
