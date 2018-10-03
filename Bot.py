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

from slackclient import SlackClient

class KarmaBot(object):
    def __init__(self):
        super(KarmaBot, self).__init__()
        self.username = 'karmachameleon'
        self.emoji = ':lizard:'
        self.verification_token = os.environ.get('VERIFICATION_TOKEN')

        # Since our app is only going to be installed in one workspace, we can use the pre-generated
        # OAuth token that Slack gave us when we created our app.
        self.client = SlackClient(os.environ.get('BOT_OAUTH_TOKEN'))
        self.karma = {}

        # TODO: Load JSON data into dictionary for saved karma values.

    def echo(self, message: str, channel_id: str):
        self.send_message(message, channel_id)

    def increment(self, item: str, channel_id: str):
        if !self.karma.get(item):
            self.karma[item] = Item()
        self.karma[item].pluses += 1
        _send_increment_message(item, channel_id)


    def decrement(self, item: str, channel_id: str):
        if !self.karma.get(item):
            self.karma[item] = Item()
        self.karma[item].minuses += 1
        _send_decrement_message(item, channel_id)

    def send_message(self, message: str, channel_id: str):
        self.client.api_call(
            'chat.postMessage',
            channel=channel_id,
            username=self.username,
            icon_emoji=self.emoji,
            text=message)

    def _send_increment_message(self, item: str, channel_id: str):
        message = 'Groovy. %s now has %s points.' % (item, self.karma[item].total_score)
        send_message(message, channel_id)

    def _send_decrement_message(self, item: str, channel_id: str):
        message = 'Brutal. %s now has %s points.' % (item, self.karma[item].total_score)
        send_message(message, channel_id)
