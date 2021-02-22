# Karma Chameleon
# Copyright (C) 2021 Dustin Schoenbrun, Will Rideout, Ben Decato
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
Defines the bot that which is passed Slack event message text and responds to them accordingly
"""

import os
import logging
import re
import json
from pathlib import Path
from typing import Tuple
import pandas as pd
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from karma_item import KarmaItem, KarmaItemEncoder
from snark import get_positive_message, get_negative_message


class KarmaBot(App):
    """Basic Bot object which is able to read incoming messages from Slack and return responses.
    The bot is also able to read karma from the json save-file, and make changes to the same.
    """

    def __init__(self, token: str, signing_secret: str) -> None:
        super().__init__(token=token, signing_secret=signing_secret)

        self.karma = {}
        self.karma_file_path = os.environ.get("KARMA_FILE_PATH")
        self.inc_regex = re.compile(r"^\S+\s?\+\+.*$")
        self.dec_regex = re.compile(r"^\S+\s?--.*$")

        # Load any saved karma
        self._load_karma_from_json_file()

        self.logger.debug("KarmaBot initialized")

    @property
    def logger(self):
        return logging.getLogger("karma_chameleon.bot")

    def _load_karma_from_json_file(self) -> None:
        self.logger.debug("Loading karma from file %s", self.karma_file_path)
        karma_file = Path(self.karma_file_path)
        if not karma_file.is_file():
            self.logger.debug("No existing karma file found. Will start fresh.")
            with open(self.karma_file_path, "w") as file_ptr:
                file_ptr.write("[]")
            return
        with open(self.karma_file_path, "r") as file_ptr:
            karma_list = json.load(file_ptr, object_hook=KarmaItem.dict_to_karmaitem)
        for item in karma_list:
            self.karma[item.name] = item

    def _save_karma_to_json_file(self) -> None:
        self.logger.debug("Saving karma JSON to file %s", self.karma_file_path)
        karma_list = list(self.karma.values())
        with open(self.karma_file_path, "w") as file_ptr:
            json.dump(karma_list, file_ptr, cls=KarmaItemEncoder)

    @staticmethod
    def _clean_up_msg_text(msg: str) -> str:
        """Clean up the passed message.
        Format should be (TOKEN(++|--) trailing_garbage).  All we need to do here is get the first
        token and strip off the last two chars.  If the token contains either a '#' or a '@', then
        that leading character is also stripped.

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

    @staticmethod
    def _check_for_self_bump(msg: str) -> bool:
        """Returns true if the passed message text contains a self-bump, i.e. the sending username
        is also present in the text as the karma target.
        """
        return msg["user"] in msg["text"]

    def increment_karma(self, msg: str) -> str:
        """Increment karma for a passed item, and pass a corresponding message to the channel inside
        which the karma was bumped to be sent.

        Arguments:
        msg -- text containing a karma event

        Returns:
        A message to be sent back to the channel in which the karma event occurred.
        """
        self.logger.debug("Processing increment message.")
        if self._check_for_self_bump(msg):
            self.logger.debug("Skipping self-increment")
            return "Ahem, no self-karma please!"

        item = self._clean_up_msg_text(msg)
        if not self.karma.get(item):
            self.karma[item] = KarmaItem(item)
        self.karma[item].pluses += 1
        snark = get_positive_message()
        total = self.karma[item].total_score
        self._save_karma_to_json_file()
        self.logger.debug("Got increment for %s", item)
        return f"{snark} {item} now has {total} points."

    def decrement_karma(self, msg: str) -> str:
        """Decrement karma for a passed item, and pass a corresponding message to the channel inside
        which the karma was bumped to be sent.

        Arguments:
        msg -- text containing a karma event

        Returns:
        A message to be sent back to the channel in which the karma event occurred.
        """
        self.logger.debug("Processing decrement message.")
        if self._check_for_self_bump(msg):
            self.logger.debug("Skipping self-decrement")
            return "Now, now.  Don't be so hard on yourself!"

        item = self._clean_up_msg_text(msg)
        if not self.karma.get(item):
            self.karma[item] = KarmaItem(item)
        self.karma[item].minuses += 1
        snark = get_negative_message()
        total = self.karma[item].total_score
        self._save_karma_to_json_file()
        self.logger.debug("Got decrement for %s", item)
        return f"{snark} {item} now has {total} points."

    def display_karma_leaderboards(self) -> Tuple[str, str, str]:
        """Prints rudimentary user and thing leaderboards.

        Returns
        A message, if applicable, a string representation of the user leaderboard, and a string
        representation of the thing leaderboard.
        """
        try:
            cur_karma = pd.read_json(self.karma_file_path)

            cur_karma["Net score"] = cur_karma.apply(
                lambda x: x["pluses"] - x["minuses"], axis=1
            )
            usr_karma = cur_karma[cur_karma["name"].str.startswith("<@")]
            thing_karma = pd.concat([cur_karma, usr_karma]).drop_duplicates(keep=False)
        except ValueError:  # Empty file or no file present
            self.logger.exception("Empty karma file or no file present, return.")
            return ("No karma yet!", "", "")

        try:
            # Add @here, @everyone, and @channel to the user list. Specific channels
            # can remain in the thing list.
            odd_karma = cur_karma[cur_karma["name"].str.startswith("<!")]
            thing_karma = pd.concat([thing_karma, odd_karma]).drop_duplicates(keep=False)
            odd_karma["name"] = odd_karma["name"].map(
                lambda x: x.lstrip("<!").rstrip(">")
            )

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

            return (
                "",
                f"User leaderboard:\n {usr_karma}",
                f"Thing leaderboard:\n {thing_karma}",
            )

        except SlackApiError as api_err:
            self.logger.error("Failed to generate leaderboard due to %s", api_err)
            return ("", "", "")
