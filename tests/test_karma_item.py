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
Unit testing for the KarmaChameleon KarmaItem class.
"""

import unittest
from unittest import TestCase
import json
from karma_chameleon.karma_item import KarmaItem, KarmaItemEncoder
from pdb import set_trace as pdb


class TestKarmaItem(TestCase):
    """Class containing unit tests for the KarmaItem class of the karma_item module."""

    @staticmethod
    def test_repr() -> None:
        """Simple test to verify __repr__ works"""
        assert repr(KarmaItem("testName", 5, 6)) == "KarmaItem('testName', 5, 6)"

    @staticmethod
    def test_str() -> None:
        """Simple test to verify __str__ works"""
        item = KarmaItem("testName", 1, 1)
        assert str(item) == "testName has 1 plus and 1 minus for a total of 0 points."

        item = KarmaItem("foobar", 3, 2)
        assert str(item) == "foobar has 3 pluses and 2 minuses for a total of 1 point."

    @staticmethod
    def test_total_score() -> None:
        """Verify the functionality of KarmaItem.total_score"""
        item = KarmaItem("foobar", 10, 4)
        assert item.total_score == 6

        item = KarmaItem("foobar", 10, 20)
        assert item.total_score == -10

    @staticmethod
    def test_dict_to_karmaitem() -> None:
        """Verify that transforming a dict into a KarmaItem works"""
        karma_dict = {
            "name": "foobar",
            "pluses": 60,
            "minuses": 10,
        }
        karma = KarmaItem.dict_to_karmaitem(karma_dict)
        assert isinstance(karma, KarmaItem)
        assert karma.name == karma_dict["name"]
        assert karma.pluses == karma_dict["pluses"]
        assert karma.minuses == karma_dict["minuses"]

        input_dict = {
            "foo": "foo",
            "bar": "bar",
        }
        output = KarmaItem.dict_to_karmaitem(input_dict)
        assert output == input_dict

    @staticmethod
    def test_json() -> None:
        # Passing an object to KarmaItemEncoder which is not a KarmaItem should use the
        # parent JSONEncoder class instead.
        """Verify that JSON serialization works"""
        encoder = KarmaItemEncoder()
        result = encoder.default(KarmaItem("foobarbaz", 9001, 10))
        assert isinstance(result, dict)
        assert result == {"name": "foobarbaz", "pluses": 9001, "minuses": 10}

        failed = False
        try:
            encoder.default({"foo": "bar"})
        except TypeError:
            failed = True
        assert failed


if __name__ == "__main__":
    unittest.main()
