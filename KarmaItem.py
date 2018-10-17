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
Implements an item that contains a number of positive and negative karma events as well as
a calculated total score.
"""
import json


class KarmaItem(object):
    def __init__(self, pluses: int = 0, minuses: int = 0):
        super(KarmaItem, self).__init__()
        self.pluses = pluses
        self.minuses = minuses

    @property
    def total_score(self):
        return self.pluses - self.minuses


class KarmaItemEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, KarmaItem):
            return {'pluses': o.pluses, 'minuses': o.minuses}
        return json.JSONEncoder.default(self, o)


