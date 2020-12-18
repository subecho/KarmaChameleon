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

"""Snark contains super-clever responses for the Chameleon to use."""

import random

positive_messages = [
    'Groovy.',
    'Radical.',
    'Bodacious.',
    'Tubular.',
    'Freakin\' sweet.',
    'Cool.',
    'Stupendous.',
    'Copacetic.',
    'Amazing.',
    'Outstanding.',
    'Jolly good.',
    'Nifty.',
    'Hot damn.',
    'Tremendous.',
    'Excellent.',
    'Most impressive.',
    'Impressive.',
    'Glorious.',
    'Sublime.',
    'Superlative job.',
    'Wooooo.',
    'Aces.',
    'Fab.',
    'Fantastic.',
    'Fan-frickin\'-tastic.',
    'Out of sight.',
    'Out of this world.',
    'Get you some.',
    'Setting an example.',
    'Can I get an amen?',
    'That\'s the bee\'s knees.',
    'Boo-yah.',
    'Yay.',
    'Yippie-ki-yay.',
    'Aye.',
    'Aye aye.',
    'As you wish.',
    'Metal.',
    'Heavy Metal.',
    ':metal:.',
    ':+1:.',
    ':beers:.',
    'Rock and roll.',
    'Money.',
    'Kobe!',
    ':100:.',
    ':1up:.',
    ':drake-yes:.',
    'Ayyyyy.',
    'This pleases the :lizard:.',
]

negative_messages = [
    'Brutal.',
    'Get Wrecked.',
    'Too bad.',
    'Unfortunate.',
    'Most unfortunate.',
    'Bummer.',
    'What a shame.',
    'Womp womp.',
    'Tsk tsk.',
    'Mic drop.',
    'Shouldn\'t have done that.',
    'Awwww.',
    'Sic semper tyranis.',
    'Bollocks.',
    'Golly.',
    'Goodness.',
    'Hardy har har.',
    'Drat.',
    'Dang.',
    'You are not going to space today.',
    'Oi! Bugger!',
    'Ouch.',
    'Ouchies',
    'Ow.',
    'As you wish.',
    'Down we go.',
    'What a drag.',
    'You have displeased :lizard:.',
    ':rage:.',
    ':drake-no:.',
    ':rage4:.',
    'Tis a shame.',
    'Bugger.',
    'Crap.',
    'Uh oh.',
    'Second rate stuff.',
    'Vile.',
    'Feeble.',
    'Shoddy.',
    'Rough.',
    'Atrocious.',
    'Abominable.',
    'Sub-par.',
]

def get_positive_message():
    """Return a random selection from positive_messages"""
    return random.choice(positive_messages)

def get_negative_message():
    """Return a random selection from negative_messages"""
    return random.choice(negative_messages)
