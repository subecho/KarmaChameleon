# Karma Chameleon
# Copyright (C) 2021 Will Rideout
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
Unit testing for the KarmaChameleon KarmaBot class.
"""

import os
from unittest import TestCase
from unittest import mock

from bot import KarmaBot
from karma_item import KarmaItem

@mock.patch.dict(
    os.environ,
    {
        "SLACK_BOT_TOKEN": "xoxb-12345-67890-deadbeef",
        "SLACK_SIGNING_SECRET": "1234567890deadbeef",
        "KARMA_FILE_PATH": "/tmp/karma",
        "PORT": "3000",
    },
)
@mock.patch("slack_bolt.App._init_middleware_list")
class TestBot(TestCase):
    """Class for all KarmaBot-related unit tests"""
    # pylint: disable=protected-access

    def cleanup(self):
        """Clean up all state left over from invoking the KarmaBot class in each test"""
        if os.path.exists(self.karma_file_path):
            os.remove(self.karma_file_path)

    def __init__(self, methodName: str) -> None:
        super().__init__(methodName=methodName)
        self.karma_file_path = "/tmp/karma"

        # Start with a clean slate for testing.
        self.cleanup()

    def test_json_file_load_write(self, _) -> None:
        """Test the functionality of JSON file loading and saving for KarmaItem objects"""
        assert not os.path.exists(self.karma_file_path)
        bot = KarmaBot(
            token=os.environ.get("SLACK_BOT_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
        )
        assert os.path.exists(self.karma_file_path)
        assert bot.karma == {}

        with open(self.karma_file_path, "w") as file_ptr:
            file_ptr.write('[{"name": "foobar", "pluses": 1, "minuses": 1}]')

        bot._load_karma_from_json_file()
        assert "foobar" in bot.karma
        assert bot.karma.get("foobar").pluses == 1
        assert bot.karma.get("foobar").minuses == 1

        bot.karma[ "baz" ] = KarmaItem("baz", 10, 10)
        bot._save_karma_to_json_file()
        with open(self.karma_file_path, "r") as file_ptr:
            lines = file_ptr.readline()
            assert "baz" in lines

        bot.karma = {}
        bot._load_karma_from_json_file()
        assert bot.karma.get("baz").pluses == 10
        assert bot.karma.get("baz").minuses == 10

        self.cleanup()

    def test_clean_up_msg_text(self, _) -> None:
        """Basic testing of Slack API event message text"""
        cases = [
            ("foobar", "foobar"),
            ("foobar", "foobar++"),
            ("foobar", "@foobar++"),
            ("foobar", "@foobar++ trailing garbage"),
            ("foobar", "foobar--"),
            ("foobar", "#foobar--"),
        ]
        bot = KarmaBot(
            token=os.environ.get("SLACK_BOT_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
        )
        for case in cases:
            exp_return_val, text = case
            event = { "text": text }
            clean_msg = bot._clean_up_msg_text(event)
            assert clean_msg == exp_return_val

        self.cleanup()

    def test_detect_self_bump(self, _) -> None:
        """Test the ability of KarmaBot to detect self-bumping in Slack API event text"""
        cases = [
            (True, {"user": "GraceHopper", "text": "GraceHopper++"}),
            (False, {"user": "AdaLovelace", "text": "GraceHopper++"}),
        ]
        bot = KarmaBot(
                token=os.environ.get("SLACK_BOT_TOKEN"),
                signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
            )

        for case in cases:
            exp_return_value, event = case
            assert bot._check_for_self_bump(event) == exp_return_value

        self.cleanup()

    def test_increment_and_decrement(self, _) -> None:
        """Test KarmaBot increment and decrement functionality"""
        bot = KarmaBot(
                token=os.environ.get("SLACK_BOT_TOKEN"),
                signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
            )
        assert bot.karma == {}
        for count in range(1,2):
            msg = bot.increment_karma({"user": "foobar", "text": "@GraceHopper++"})
            assert f"GraceHopper now has {count} points." in msg
            assert "GraceHopper" in bot.karma

        assert "AdaLovelace" not in bot.karma
        for count in range(1,2):
            msg = bot.decrement_karma({"user": "foobar", "text": "@AdaLovelace--"})
            assert f"AdaLovelace now has -{count} points." in msg
            assert "AdaLovelace" in bot.karma
        self.cleanup()
