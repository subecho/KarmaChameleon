# Karma Chameleon
# Copyright (C) 2021 Dustin Schoenbrun, Will Rideout
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
KarmaChameleon

A simple Slack bot which allows users to assign karma to each other or things via the use of "++"
and "--" in messages.
"""

import re
import os
import logging
from logging.handlers import RotatingFileHandler
import json
from pathlib import Path
import pandas as pd
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from snark import get_positive_message, get_negative_message
from karma_item import KarmaItem, KarmaItemEncoder

# There is only one logger, with three different sub-loggers.  All loggers use the same file
# destination, and line format.  The logger with UID "karma_chameleon" is used to log events for the
# main app, i.e. the Flask app.  karma_chameleon.event_manager logs events and debug info pertaining
# to the event_manager.py methods.  karma_chameleon.bot logs events and debug info pertaining to the
# methods of the KarmaBot class.
#
# If the logs dir does not exit, make it.
if not os.path.exists("logs"):
    os.makedirs("logs")

# Create the "main" logger.  This logger has the file destination and line format that is inherited
# by all sub-loggers.
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

# karmaBot = KarmaBot() WRIDEOUT DO WE NEED THIS?  WHY NOT JUST INHERIT FROM APP?
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

karma = {}
karma_file_path = os.environ.get("KARMA_FILE_PATH")


def load_karma_from_json_file():
    """Load karma from the JSON file stored at the KARMA_FILE_PATH environment variable"""
    logger.debug("Loading karma from file %s", karma_file_path)
    karma_file = Path(karma_file_path)
    if not karma_file.is_file():
        logger.debug("No existing karma file found. Will start fresh.")
        print("No existing file found. Will start fresh.")
        with open(karma_file_path, "w") as file_ptr:
            file_ptr.write("[]")
        return
    with open(karma_file_path, "r") as file_ptr:
        karma_list = json.load(file_ptr, object_hook=KarmaItem.dict_to_karmaitem)
    for item in karma_list:
        karma[item.name] = item


def save_karma_to_json_file():
    """Save all local karma to the JSON file stored at the KARMA_FILE_PATH environment variable"""
    logger.debug("Saving karma JSON to file %s", karma_file_path)
    karma_list = list(karma.values())
    with open(karma_file_path, "w") as file_ptr:
        json.dump(karma_list, file_ptr, cls=KarmaItemEncoder)


load_karma_from_json_file()


def clean_up_msg_text(msg):
    """Clean up the passed message.
    Format should be (TOKEN(++|--) trailing_garbage).  All we need to do here is get the first
    token and strip off the last two chars.  If the token contains either a '#' or a '@', then that
    leading character is also stripped.

    Arguments:
    msg -- text which contains a karma operation

    Returns:
    Cleaned message
    """
    msg = msg["text"].split()[0]  # remove trailing garbage
    if msg[-2:] in ("++", "--"):
        msg = msg[:-2]
    if msg[0] in ("#", "@"):
        msg = msg[1:]
    return msg


def check_for_self_bump(msg):
    """Returns true if the passed message text contains a self-bump, i.e. the sending username is
    also present in the text as the karma target.
    """
    return msg["user"] in msg["text"]


@app.message(re.compile(r"^\S+\s?\+\+.*$"))
def increment(message, say):
    """Increment karma for a passed item, and send a corresponding message to the channel inside
    which the karma was bumped.

    Arguments:
    message -- dictionary representation of the message which contains a karma operation
    say -- method for printing back to the same channel from which the command was run
    """
    logger.debug("Processing increment message.")
    if check_for_self_bump(message):
        logger.debug("Skipping self-increment")
        say("Ahem, no self-karma please!")
    else:
        item = clean_up_msg_text(message)
        if not karma.get(item):
            karma[item] = KarmaItem(item)
        karma[item].pluses += 1
        snark = get_positive_message()
        total = karma[item].total_score
        say(f"{snark} {item} now has {total} points.")
        save_karma_to_json_file()
        logger.debug("Got increment for %s", item)


@app.message(re.compile(r"^\S+\s?--.*$"))
def decrement(message, say):
    """Decrement karma for a passed item, and send a corresponding message to the channel inside
    which the karma was bumped.

    Arguments:
    message -- dictionary representation of the message which contains a karma operation
    say -- method for printing back to the same channel from which the command was run
    """
    logger.debug("Processing decrement message.")
    if check_for_self_bump(message):
        logger.debug("Skipping self-decrement")
        say("Now, now.  Don't be so hard on yourself!")
    else:
        item = clean_up_msg_text(message)
        if not karma.get(item):
            karma[item] = KarmaItem(item)
        karma[item].minuses += 1
        snark = get_negative_message()
        total = karma[item].total_score
        say(f"{snark} {item} now has {total} points.")
        save_karma_to_json_file()
        logger.debug("Got decrement for %s", item)


@app.command("/ec_leaderboard")
def show_leaderboard(ack, say, _):
    """Print user and thing leaderboards, sorted by total karma accrued.

    Arguments:
    ack -- acknowledgement method, called to acknowledge the command was received
    say -- method for printing back to the same channel from which the command was run
    """
    # Must acknowledge the command was run.
    ack()
    try:
        cur_karma = pd.read_json(karma_file_path)

        cur_karma["Net score"] = cur_karma.apply(
            lambda x: x["pluses"] - x["minuses"], axis=1
        )
        usr_karma = cur_karma[cur_karma["name"].str.startswith("<@")]
        thing_karma = pd.concat([cur_karma, usr_karma]).drop_duplicates(keep=False)
    except ValueError:  # Empty file or no file present
        logger.exception("Empty karma file or no file present, return.")
        say("No karma yet!")
        return

    try:
        # Add @here, @everyone, and @channel to the user list. Specific channels
        # can remain in the thing list.
        odd_karma = cur_karma[cur_karma["name"].str.startswith("<!")]
        thing_karma = pd.concat([thing_karma, odd_karma]).drop_duplicates(keep=False)
        odd_karma["name"] = odd_karma["name"].map(lambda x: x.lstrip("<!").rstrip(">"))

        web_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
        request = web_client.users_list()
        rows = []
        if request["ok"]:
            for item in request["members"]:
                rows.append([item["id"], item["name"]])
        ids_to_names = pd.DataFrame(rows, columns=["name", "real_name"])
        ids_to_names["name"] = "<@" + ids_to_names["name"] + ">"
        usr_karma = pd.merge(usr_karma, ids_to_names, on="name", how="inner")
        usr_karma["name"] = usr_karma["real_name"]
        del usr_karma["real_name"]

        usr_karma = usr_karma.append(odd_karma)

        usr_karma = usr_karma.sort_values(by=["Net score"], ascending=False)
        thing_karma = thing_karma.sort_values(by=["Net score"], ascending=False)
        thing_karma = thing_karma.head(10)
        usr_karma = usr_karma.head(10)

        usr_karma = "```" + usr_karma.to_markdown(index=False) + "```"
        thing_karma = "```" + thing_karma.to_markdown(index=False) + "```"

        say(f"User leaderboard:\n {usr_karma}")
        say(f"Thing leaderboard:\n {thing_karma}")
    except SlackApiError as api_err:
        logger.error("Failed to generate leaderboard due to %s", api_err)


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
