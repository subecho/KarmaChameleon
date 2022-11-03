# Karma Chameleon Copyright (C) 2021 Will Rideout
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
Unit testing for the KarmaChameleon KarmaBot class.
"""
import json
import os
from unittest import TestCase
from unittest import mock

from slack_sdk.errors import SlackApiError

from karma_chameleon.bot import KarmaBot
from karma_chameleon.karma_item import KarmaItem


@mock.patch.dict(
    os.environ,
    {
        "SLACK_BOT_TOKEN": "xoxb-12345-67890-deadbeef",
        "KARMA_FILE_PATH": "/tmp/karma",
    },
)
@mock.patch("slack_bolt.App._init_middleware_list")
class TestBot(TestCase):
    """Class for all KarmaBot-related unit tests"""

    # pylint: disable=protected-access

    def cleanup(self) -> None:
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
        )
        assert os.path.exists(self.karma_file_path)
        assert not bot.karma  # No karma from empty file.

        with open(self.karma_file_path, "w", encoding="utf-8") as file_ptr:
            file_ptr.write('[{"name": "foobar", "pluses": 1, "minuses": 1}]')

        bot._load_karma_from_json_file()
        assert "foobar" in bot.karma
        assert bot.karma.get("foobar").pluses == 1
        assert bot.karma.get("foobar").minuses == 1

        bot.karma["baz"] = KarmaItem("baz", 10, 10)
        bot._save_karma_to_json_file()
        with open(self.karma_file_path, "r", encoding="utf-8") as file_ptr:
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
        )
        for case in cases:
            exp_return_val, text = case
            event = {"text": text}
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
        )

        for case in cases:
            exp_return_value, event = case
            assert bot._check_for_self_bump(event) == exp_return_value

        self.cleanup()

    def test_detect_url(self, _) -> None:
        """Test the ability of KarmaBot to detect a URL which contains either the --
        token.
        """
        cases = [
            (True, {"user": "GraceHopper", "text": "https://www.example--.com"}),
            (False, {"user": "GraceHopper", "text": "https://www.example.com"}),
        ]
        bot = KarmaBot(
            token=os.environ.get("SLACK_BOT_TOKEN"),
        )

        for case in cases:
            exp_return_value, event = case
            assert bot._check_for_url(event) == exp_return_value

    def test_increment_and_decrement(self, _) -> None:
        """Test KarmaBot increment and decrement functionality"""
        bot = KarmaBot(
            token=os.environ.get("SLACK_BOT_TOKEN"),
        )
        assert not bot.karma
        for count in range(1, 2):
            msg = bot.increment_karma({"user": "foobar", "text": "@GraceHopper++"})
            assert f"GraceHopper now has {count} points" in msg
            assert "GraceHopper" in bot.karma

        assert "AdaLovelace" not in bot.karma
        for count in range(1, 2):
            msg = bot.decrement_karma({"user": "foobar", "text": "@AdaLovelace--"})
            assert f"AdaLovelace now has -{count} points" in msg
            assert "AdaLovelace" in bot.karma

        msg = bot.increment_karma({"user": "GraceHopper", "text": "@GraceHopper++"})
        assert msg == "Ahem, no self-karma please!"
        msg = bot.decrement_karma({"user": "GraceHopper", "text": "@GraceHopper--"})
        assert msg == "Now, now. Don't be so hard on yourself!"
        self.cleanup()

    @mock.patch("slack_sdk.WebClient.users_list")
    def test_leaderboard(self, wc_users_list, _) -> None:
        """Basic testing of the display_leaderboards functionality.

        Arguments:
        wc_users_list -- Mocked out version of the WebClient.client.users_list method.
                         Populated
                         by the @patch decorator.
        """
        wc_users_list.return_value = {
            "ok": True,
            "members": [
                {
                    "id": "U12345",
                    "real_name": "Ada Lovelace",
                },
                {
                    "id": "U67890",
                    "real_name": "Grace Hopper",
                },
            ],
        }
        users_to_ids = {"<@U12345>": "Ada Lovelace", "<@U67890>": "Grace Hopper"}

        bot = KarmaBot(
            token=os.environ.get("SLACK_BOT_TOKEN"),
        )

        # Start by testing how an empty or missing karma file is handled.
        assert bot.display_karma_leaderboards() == ("No karma yet!", "", "")

        # Begin by populating a karma test file.
        test_items = [
            "testA",
            "testB",
            "<@U12345>",
            "<@U67890>",
        ]
        test_karma = [
            (5, 0),
            (6, 1),
            (7, 2),
            (8, 3),
        ]

        with open(self.karma_file_path, "w", encoding="utf-8") as json_file:
            json.dump(
                [
                    {"name": item, "pluses": 5 + i, "minuses": i}
                    for i, item in enumerate(test_items)
                ],
                json_file,
            )

        _, users_text, things_text = bot.display_karma_leaderboards()
        # Remove the trailing "```" from markdown syntax, then split by line,
        # ignoring the first three lines which are header.
        things_text = things_text[:-3].split("\n")[3:]
        for item, karma, text in zip(test_items[:2], test_karma[:2], things_text):
            found = [t.strip() for t in text.split("|") if t]
            expected = [item, str(karma[0]), str(karma[1]), str(karma[0] - karma[1])]
            assert found == expected

        users_text = users_text[:-3].split("\n")[3:]
        for item, karma, text in zip(test_items[2:], test_karma[2:], users_text):
            found = [t.strip() for t in text.split("|") if t]
            expected = [
                users_to_ids[item],
                str(karma[0]),
                str(karma[1]),
                str(karma[0] - karma[1]),
            ]
            assert found == expected

        self.cleanup()

    @mock.patch("slack_sdk.WebClient")
    def test_leaderboard_exceptions(self, web_client, _) -> None:
        """Basic testing of the leaderboard method's ability to handle exceptions

        Arguments:
        web_client -- Mocked out version of the WebClient class.
                      Populated by the @patch decorator
        """
        web_client.side_effect = SlackApiError("test error", None)

        with open(self.karma_file_path, "w", encoding="utf-8") as json_file:
            json.dump(
                [{"name": "foobar", "pluses": 9000, "minuses": 9000}],
                json_file,
            )

        bot = KarmaBot(
            token=os.environ.get("SLACK_BOT_TOKEN"),
        )

        msg, user_text, thing_text = bot.display_karma_leaderboards()
        assert not msg and not user_text and not thing_text
        self.cleanup()
