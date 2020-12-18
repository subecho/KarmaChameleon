# Karma Chameleon
# Copyright (C) 2018 Dustin Schoenbrun
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
Defines the bot that is listening for Slack events and responds to them accordingly
"""
import json
import os
from pathlib import Path

from slack import WebClient

from KarmaItem import KarmaItem, KarmaItemEncoder
from snark import get_positive_message, get_negative_message

class KarmaBot(object):
    """Basic Bot object which is able to read incoming messages from Slack and send responses.
    The bot is also able to read karma from the json save-file, and make changes to the same.
    """
    def __init__(self):
        super(KarmaBot, self).__init__()
        self.username = 'Karma Chameleon'
        self.emoji = ':lizard:'
        self.verification_token = os.environ.get('VERIFICATION_TOKEN')

        # Since our app is only going to be installed in one workspace, we can use the pre-generated
        # OAuth token that Slack gave us when we created our app.
        self.oauth_token = os.environ.get('BOT_OAUTH_TOKEN')
        self.client = WebClient(self.oauth_token)
        self.karma = {}
        self.karma_file_path = os.environ.get('KARMA_FILE_PATH')

        self._load_karma_from_json_file()

    def echo(self, message: str, channel_id: str):
        self.send_message(message, channel_id)

    def increment(self, item: str, channel_id: str):
        if not self.karma.get(item):
            self.karma[item] = KarmaItem(item)
        self.karma[item].pluses += 1
        self._send_increment_message(item, channel_id)
        self._save_karma_to_json_file()

    def decrement(self, item: str, channel_id: str):
        if not self.karma.get(item):
            self.karma[item] = KarmaItem(item)
        self.karma[item].minuses += 1
        self._send_decrement_message(item, channel_id)
        self._save_karma_to_json_file()

    def chastise(self, inc: bool, channel_id: str):
        if inc:
            self._send_chastise_message(channel_id)
        else:
            self._send_encouragement_message(channel_id)

    def send_message(self, message: str, channel_id: str):
        self.client.api_call(
            api_method='chat.postMessage',
            json={
                    'token': self.oauth_token,
                    'channel': channel_id,
                    'text': message,
                    'username': self.username,
                    'icon_emoji': self.emoji,
            })

    def _send_increment_message(self, item: str, channel_id: str):
        message = '%s %s now has %s points.' % (get_positive_message(), item, self.karma[item].total_score)
        self.send_message(message, channel_id)

    def _send_decrement_message(self, item: str, channel_id: str):
        message = '%s %s now has %s points.' % (get_negative_message(), item, self.karma[item].total_score)
        self.send_message(message, channel_id)

    def _send_chastise_message(self, channel_id: str):
        self.send_message('Ahem, no self-bumping...', channel_id)

    def _send_encouragement_message(self, channel_id: str):
        self.send_message("Now, now.  Don't be so hard on yourself!", channel_id)

    def _save_karma_to_json_file(self):
        karma_list = list(self.karma.values())
        with open(self.karma_file_path, 'w') as fp:
            json.dump(karma_list, fp, cls=KarmaItemEncoder)

    def _load_karma_from_json_file(self):
        karma_file = Path(self.karma_file_path)
        if not karma_file.is_file():
            print('No existing file found. Will start fresh.')
            return
        with open(self.karma_file_path, 'r') as fp:
            karma_list = json.load(fp, object_hook=KarmaItem.dict_to_karmaitem)
        for item in karma_list:
            self.karma[item.name] = item
