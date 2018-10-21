# Karma Chameleon
A simple karma bot for Slack. 

This is a simple, standalone Slack bot that watches for “karma events” and will keep track of scores for users and topics.

## Adding Karma
In a channel where Karma Chameleon is present, do the following to add a point to a user or topic.

`@user++`

## Removing Karma
In a channel where Karma Chameleon is present, do the following to remove a point from the user or topic.

`@user—-`

## Setting up a Development Environment
Karma Chameleon relies on `pip` to install its dependencies and is easiest to develop with a Python Virtual Environment.

```
$ git clone https://github.com/subecho/KarmaChameleon.git
$ cd KarmaChameleon
$ virtualenv .venv
$ source .venv/bin/activate
(.venv) $ pip install -r requirements.txt
```

## Running the Bot in a Development Environment
Before running the code, we need to do some initial setup on the Slack side so that Slack knows who we are, we are who we say we are, and which events we wish to subscribe to. You will need to create a new app in Slack and add the `channels:history` and `chat:write:bot` scopes to it.

There are two steps to running the bot on your local machine: running the actual Python code and forwarding the port that the Flask server is running on to a publicly accessible URL. I used [ngrok](https://ngrok.com) to do this and it’s available via Brew on macOS.

In one terminal window, run:
`python3 EventManager.py`

After running that, in another terminal window, run:
`ngrok http 5000`

This command will output an https URL that can be used to interact with the bot. You will want to paste this URL into the _Request URL_ field in the _Event Subscriptions_ page for your app. You will also want to make sure that you add the `message.channels` event to the subscribed events for the bot.
