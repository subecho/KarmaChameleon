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
Provides the routing and management of interactions between Slack and the karma bot.
"""

import re
import os
import logging
from logging.handlers import RotatingFileHandler
from slack_bolt import App
from pdb import set_trace as pdb

# There is only one logger, with three different sub-loggers.  All loggers use the same file
# destination, and line format.  The logger with UID "karma_chameleon" is used to log events for the
# main app, i.e. the Flask app.  karma_chameleon.event_manager logs events and debug info pertaining
# to the event_manager.py methods.  karma_chameleon.bot logs events and debug info pertaining to the
# methods of the KarmaBot class.
#
# If the logs dir does not exit, make it.
if not os.path.exists('logs'):
    os.makedirs('logs')

# Create the "main" logger.  This logger has the file destination and line format that is inherited
# by all sub-loggers.
logger = logging.getLogger('karma_chameleon')
logger.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler('logs/karma_chameleon.log', maxBytes=10_000_000, backupCount=3)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s[%(funcName)s]: %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Create a sub-logger for the app methods.
app_logger = logging.getLogger('karma_chameleon.app')

# karmaBot = KarmaBot() WRIDEOUT DO WE NEED THIS?  WHY NOT JUST INHERIT FROM APP?
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

def clean_up_msg_text(msg):
    msg = msg['text'].split()[0] # remove trailing garbage
    if msg[-2:] in ('++', '--'):
        msg = msg[:-2]
    if msg[0] in ('#', '@'):
        msg = msg[1:]
    return msg

def check_for_self_bump(msg):
    return msg['user'] in msg['text']

@app.message(re.compile(r"^\S+\s?\+\+.*$"))
def got_increment(message, say):
    app_logger.debug("Processing increment message.")
    if check_for_self_bump(message):
        app_logger.debug("Skipping self-increment")
        say('Ahem, no self-karma please!')
    else:
        msg = clean_up_msg_text(message)
        say(f'Got increment for {msg}')
        app_logger.debug(f"Got increment for {msg}.")

@app.message(re.compile(r"^\S+\s?--.*$"))
def got_decrement(message, say):
    app_logger.debug("Processing decrement message.")
    if check_for_self_bump(message):
        app_logger.debug("Skipping self-decrement")
        say("Now, now.  Don't be so hard on yourself!")
    else:
        msg = clean_up_msg_text(message)
        say(f'Got decrement for {msg}')
        app_logger.debug(f"Got decrement for {msg}.")

#@app.command("/leaderboard")
#def repeat_text(ack, say, command):
    # Acknowledge command request
#    ack()
#    say(f"{command['text']}")

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))