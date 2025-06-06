# Karma Chameleon Copyright (C) 2023 Dustin Schoenbrun, Will Rideout, Ben Decato
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
Defines the bot that which is passed Slack event message text and responds to them
accordingly
"""

import json
import logging
import os
import re
from collections import namedtuple
from pathlib import Path
from typing import Tuple
from typing import Union

from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from karma_chameleon.karma_item import KarmaItem, KarmaItemEncoder
from karma_chameleon.snark import get_positive_message, get_negative_message


class KarmaBot(App):
    """Basic Bot object which is able to read incoming messages from Slack and return
    responses.  The bot is also able to read karma from the json save-file, and make
    changes to the same.
    """

    def __init__(self, token: str) -> None:
        super().__init__(token=token)

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
            with open(self.karma_file_path, "w", encoding="utf-8") as file_ptr:
                file_ptr.write("[]")
            return
        with open(self.karma_file_path, "r", encoding="utf-8") as file_ptr:
            karma_list = json.load(file_ptr, object_hook=KarmaItem.dict_to_karma_item)
        for item in karma_list:
            self.karma[item.name] = item

    def _save_karma_to_json_file(self) -> None:
        self.logger.debug("Saving karma JSON to file %s", self.karma_file_path)
        karma_list = list(self.karma.values())
        with open(self.karma_file_path, "w", encoding="utf-8") as file_ptr:
            json.dump(karma_list, file_ptr, cls=KarmaItemEncoder)

    @staticmethod
    def _clean_up_msg_text(msg: dict) -> str:
        """Clean up the passed message.  Format should be (TOKEN(++|--) trailing_garbage).
        All we need to do here is get the first token and strip off the last two chars.
        If the token contains either a '#' or a '@', then that leading character is also
        stripped.

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
    def _check_for_self_bump(msg: dict) -> bool:
        """Returns true if the passed message text contains a self-bump, i.e. the sending
        username is also present in the text as the karma target.
        """
        return msg["user"] in msg["text"]

    @staticmethod
    def _check_for_url(msg: dict) -> bool:
        """Returns True if the passed message text contains the -- token as part of a
        larger URL string.

        The URL regex is shamelessly copied from https://urlregex.com/.
        """
        url_re = re.compile(r"https?://(?:[\w]|[$-_]|[!*\(\),]|(%[0-9a-fA-F][0-9a-fA-F]))+")

        for word in msg["text"].split():
            # As of the writing of this code, "++" is not able to be included, unencoded,
            # in a URL.
            if "--" in word:
                return re.match(url_re, word) is not None
        return False

    def get_username_from_uid(self, uid: str) -> Union[str, None]:
        """Fetch the username corresponding to the passed UID string."""
        if not uid:
            return None

        try:
            client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
            result = client.users_info(user=uid)
            return result["user"]["real_name"]

        except SlackApiError as err:
            self.logger.error("Error fetching username for %s: %s", uid, err)
            return None

    def increment_karma(self, msg: dict) -> str:
        """Increment karma for a passed item, and pass a corresponding message to the
        channel inside which the karma was bumped to be sent.

        Arguments:
        msg -- text containing a karma event

        Returns:
        The message to be sent back to the channel in which the karma event occurred.
        """
        self.logger.debug("Processing increment message.")
        if self._check_for_self_bump(msg):
            self.logger.debug("Skipping self-increment")
            return "Ahem, no self-karma please!"

        tail = f", thanks to {self.get_username_from_uid(msg['user'])}."

        item = self._clean_up_msg_text(msg)
        if not self.karma.get(item):
            self.karma[item] = KarmaItem(item)
        self.karma[item].pluses += 1
        snark = get_positive_message()
        total = self.karma[item].total_score
        self._save_karma_to_json_file()
        self.logger.debug("Got increment for %s", item)
        return f"{snark} {item} now has {total} points{tail}"

    def decrement_karma(self, msg: dict) -> str:
        """Decrement karma for a passed item, and pass a corresponding message to the
        channel inside which the karma was bumped to be sent.

        Arguments:
        msg -- text containing a karma event

        Returns:
        A message to be sent back to the channel in which the karma event occurred.
        """
        self.logger.debug("Processing decrement message.")
        if self._check_for_self_bump(msg):
            self.logger.debug("Skipping self-decrement")
            return "Now, now. Don't be so hard on yourself!"

        if self._check_for_url(msg):
            return None  # Fail silently... no need to respond to the user.

        item = self._clean_up_msg_text(msg)
        if not self.karma.get(item):
            self.karma[item] = KarmaItem(item)
        self.karma[item].minuses += 1
        snark = get_negative_message()
        total = self.karma[item].total_score
        self._save_karma_to_json_file()
        self.logger.debug("Got decrement for %s", item)
        return f"{snark} {item} now has {total} points."
