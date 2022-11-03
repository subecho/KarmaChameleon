# Karma Chameleon
![](https://github.com/subecho/KarmaChameleon/workflows/CI%20Tests/badge.svg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A simple karma bot for Slack.

This is a simple, standalone Slack bot that watches for “karma events” and will keep track
of scores for users and topics.

## Adding Karma
In a channel where Karma Chameleon is present, do the following to add a point to a user
or topic.

`@user++`

`subject++`

## Removing Karma
In a channel where Karma Chameleon is present, do the following to remove a point from the
user or topic.

`@user—-`

`subject--`

Note that decrementing or incrementing a user's own karma (the self-bump) is not a valid
operation. You will be chastised by the Chameleon.

## Setting up a Development Environment
Karma Chameleon relies on `pip` to install its dependencies and is easiest to develop with
a Python Virtual Environment.

```
$ git clone https://github.com/subecho/KarmaChameleon.git
$ cd KarmaChameleon
$ python3 -m venv .venv
$ source .venv/bin/activate
(.venv) $ python3 -m pip install -r requirements.txt
```

## Running the Bot in a Development Environment
Before running the code, we need to do some initial setup on the Slack side so that Slack
knows who we are, we are who we say we are, and which events we wish to subscribe to. You
will need to create a new app in Slack and add the following scopes:

**Bot Token Scopes:**
- channels:history
- channels:join
- channels:manage
- chat:write
- chat:write.customize
- chat:write.public
- commands
- users:read

**App-Level Tokens Scopes:**
- connections:write

**User Token Scopes:**
- channels:history

There are two steps to testing the bot on your local machine: running the code and
forwarding the port on which Karma Chameleon is listening to some publicly available URL.
The CLI tool [ngrok](https://ngrok.com) may be used to do this.

The following environment variables must be present in order for Karma Chameleon to
function:
- `SLACK_BOT_TOKEN`: populated with the contents of the SLACK_BOT_TOKEN OAuth key in the
  Slack App OAuth settings
- `SLACK_APP_TOKEN`: populated with the contents of an App-Level Token specifically
  generated for use with socket mode, which may be found in Slack App Basic Information
- `KARMA_FILE_PATH`: the path to which Karma Chameleon will create and maintain a JSON
  record of all karma.

In one terminal window, run: `python3 karma_chameleon.py`

After running that, in another terminal window, run: `ngrok http 3000`

This command will output an https URL that can be used to interact with the bot. You will
want to paste this URL into the _Request URL_ field in the _Event Subscriptions_ page for
your app. The format of the URL should be "<ngrok URL>/slack/events".  You will also want
to make sure that you add the `message.channels` event to the subscribed events for the
bot.  For slash-command support, a new command must be added with the request URL also
being the ngrok URL in the format of "<ngrok URL>/slack/events".

The Karma Chameleon icon was made by [Eucalyp](https://www.flaticon.com/authors/eucalyp)
from www.flaticon.com.
