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
Unit testing for the KarmaChameleon App proper.
"""

import contextlib
import io
import os
from unittest import TestCase
from unittest import mock

from slack_bolt import BoltResponse, Ack

with mock.patch.dict(
    os.environ,
    {
        "SLACK_BOT_TOKEN": "xoxb-12345-67890-deadbeef",
        "KARMA_FILE_PATH": "/tmp/karma",
    },
):
    with mock.patch("slack_bolt.App._init_middleware_list"):
        from karma_chameleon.main import (
            handle_no_karma_op,
            increment,
            decrement,
        )


class TestApp(TestCase):
    """Class containing unit tests for the app functionality of the main karma_chameleon
    module."""

    callable_called = "next_method was called"
    test_msg = {"event": {"type": "message", "text": "foobarbaz"}}

    def _next_method(self):
        return self.callable_called

    @staticmethod
    def _say_method(msg):
        print(msg)

    class SpoofAck(Ack):  # pylint: disable=too-few-public-methods
        """Child class of the Slack Bolt API Spoof class, which allows us to verify ack
        was called."""

        ack_msg = "Ack was called!"

        def __call__(self, **kwargs):  # pylint: disable=signature-differs
            print(self.ack_msg)

    def test_handle_no_karma_op(self) -> None:
        """Test for verifying the behavior of the middleware which allows the kc bot to
        skip any incoming event which does not contain a karma operation
        """
        # import karma_chameleon as kc # pylint: disable=import-outside-toplevel

        # Spoof some message payloads
        bodies = [
            (
                {"command": "foobar"},
                lambda x: x == self.callable_called,
            ),  # Spoof a command
            (
                {"event": {"type": "message", "text": "foobarbaz"}},
                lambda x: isinstance(x, BoltResponse),
            ),  # No karma event
            (
                {"event": {"type": "message"}},
                lambda x: isinstance(x, BoltResponse),
            ),  # No text in event body
            (
                {"event": {"type": "message", "text": "foobarbaz++"}},
                lambda x: x == self.callable_called,
            ),  # ++ karma event
            (
                {"event": {"type": "message", "text": "foobarbaz--"}},
                lambda x: x == self.callable_called,
            ),  # -- karma event
        ]

        for body, verify_method in bodies:
            retval = handle_no_karma_op(body, self._next_method)
            assert verify_method(retval)

    @mock.patch("karma_chameleon.bot.KarmaBot.increment_karma")
    def test_increment(self, app_inc_karma) -> None:
        """Test the method of the main app which calls the bot increment."""
        msg = "Got the message!"
        app_inc_karma.return_value = msg

        with contextlib.redirect_stdout(io.StringIO()) as out:
            increment(self.test_msg, self._say_method)
            assert app_inc_karma.inc_karma.called_with(self.test_msg)
            assert out.getvalue() == msg + "\n"

    @mock.patch("karma_chameleon.bot.KarmaBot.decrement_karma")
    def test_decrement(self, app_dec_karma) -> None:
        """Test the method of the main app which calls the bot decrement."""
        for msg in ["Got the message!", ""]:
            app_dec_karma.return_value = msg

            with contextlib.redirect_stdout(io.StringIO()) as out:
                decrement(self.test_msg, self._say_method)
                assert app_dec_karma.inc_karma.called_with(self.test_msg)
                assert out.getvalue() == (msg + "\n" if msg else msg)

    @mock.patch("karma_chameleon.bot.KarmaBot.decrement_karma")
    def test_decrement_no_msg(self, app_dec_karma) -> None:
        """Test the method of the main app which calls the bot decrement."""
        msg = ""
        app_dec_karma.return_value = msg

        with contextlib.redirect_stdout(io.StringIO()) as out:
            decrement(self.test_msg, self._say_method)
            assert app_dec_karma.inc_karma.called_with(self.test_msg)
            assert out.getvalue() == msg
