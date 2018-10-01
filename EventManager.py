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

import json
from Bot import KarmaBot
from flask import Flask, request, make_response

karmaBot = KarmaBot()
app = Flask(__name__)

def handle_event(event_type, event):
    """
    Routes events from Slack to our KarmaBot instance by type and subtype.

    Keyword arguments:
    event_type -- A string representing the type of event received from Slack.
    event -- The dictionary representing the JSON event from Slack.

    Returns:
    A response object with 200 OK if there was a valid event handler or 500 if there was no valid
    event handler for the given event type.
    """
    slack_event = event['event']
    team_id = event['team_id']
    channel_id = slack_event['channel']
    # Ensure that the message we got is not from the bot itself
    if event_type == 'message' and slack_event.get('subtype') != 'bot_message':
        # Write the message back from the bot.
        message = slack_event['text']
        karmaBot.echo(message, channel_id)
        return make_response('We got a message', 200)

    # At this point, we don't have a handler for this response, so send a response saying so.
    return make_response('No handler for %s' % event_type, 200, {'X-Slack-No-Retry': 1})

@app.route('/karma', methods=['GET', 'POST'])
def listen():
    """
    Listens for incoming events and routes them to the proper handler in the bot
    """
    event = json.loads(request.data)

    if 'challenge' in event:
        return _create_challenge_response(event['challenge'])

    if karmaBot.verification_token != event.get('token'):
        print('Verification Token is Invalid, our token: %s, token provided: %s' % (
            karmaBot.verification_token, event.get('token')))
        return _create_invalid_verification_token_response(event.get('token'))

    if 'event' in event:
        event_type = event['event']['type']     
        return handle_event(event_type, event)

def _create_challenge_response(challenge: str):
    return make_response(challenge, 200, {'content_type': 'application/json'})

def _create_invalid_verification_token_response(bad_token: str):
    message = 'Invalid Slack verification token: %s\nOur Bot has: %s' % (bad_token, 
                                                                        karmaBot.verification_token)
    # Adding 'X-Slack-No-Retry': 1 to our response header turns off Slack's auto retries while we
    # develop.
    return make_response(message, 403, {'X-Slack-No-Retry': 1})


if __name__ == '__main__':
    app.run(debug=True)
