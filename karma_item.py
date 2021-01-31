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
Implements an item which stores a name and that thing's karma score as a factor of number of pluses
and minuses.
"""
import json


class KarmaItem:
    """Object representation of a thing, and the karma associated with that thing."""

    def __init__(self, name: str, pluses: int = 0, minuses: int = 0):
        super().__init__()
        self.name = name
        self.pluses = pluses
        self.minuses = minuses

    def __repr__(self):
        return self.__class__.__name__ + "({!r}, {!r}, {!r})".format(
            self.name, self.pluses, self.minuses
        )

    def __str__(self):
        if self.pluses == 1:
            pluses_msg = " has 1 plus "
        else:
            pluses_msg = " has %s pluses " % self.pluses

        if self.minuses == 1:
            minuses_msg = "and 1 minus "
        else:
            minuses_msg = "and %s minuses " % self.minuses

        if self.total_score == 1:
            total_msg = "for a total of 1 point."
        else:
            total_msg = "for a total of %s points." % self.total_score

        return self.name + pluses_msg + minuses_msg + total_msg

    @property
    def total_score(self):
        """
        Calculated property which returns the total score which is pluses - minuses.

        Returns:
        The current total score of the KarmaItem.
        """
        return self.pluses - self.minuses

    @staticmethod
    def dict_to_karmaitem(a_dict: dict):
        """
        Return a KarmaItem if a_dict is a representation of a KarmaItem or a_dict unmodified
        otherwise.

        This method is intended to be used as the object_hook parameter when we call json.load() to
        load our existing karma items from a saved JSON file into memory in our KarmaBot object.
        :param a_dict: A dictionary representing a KarmaItem object.
        :return: A new KarmaItem object with the values from a_dict or a_dict if it's not a
        representation of a KarmaItem
        """
        key_list = a_dict.keys()
        if "name" in key_list and "pluses" in key_list and "minuses" in key_list:
            return KarmaItem(a_dict["name"], a_dict["pluses"], a_dict["minuses"])
        return a_dict


class KarmaItemEncoder(json.JSONEncoder):
    """
    This class defines how to JSON Serialize our KarmaItem class. We do this via implementing the
    default() function which defines what to do with objects that the JSON library is attempting to
    serialize. If the object happens to be an instance of KarmaItem, we return the appropriate
    representation of the object, otherwise we just call the superclass's implementation of default
    and let it handle the object.
    """

    def default(self, o):
        if isinstance(o, KarmaItem):
            return {"name": o.name, "pluses": o.pluses, "minuses": o.minuses}
        return super().default(o)
