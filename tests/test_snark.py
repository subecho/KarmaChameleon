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
Unit testing for the KarmaChameleon snark.
"""

import unittest
from unittest import TestCase
import snark


class TestSnark(TestCase):
    """Simple unit test class for exercising snark"""

    def test_snark(self) -> None:
        """Verify get_positive_message and get_negative_message"""
        msg = snark.get_positive_message()
        assert msg
        assert msg in snark.positive_messages
        assert msg not in snark.negative_messages

        msg = snark.get_negative_message()
        assert msg
        assert msg in snark.negative_messages
        assert msg not in snark.positive_messages


if __name__ == "__main__":
    unittest.main()
