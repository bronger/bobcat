#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright © 2007, 2008 Torsten Bronger <bronger@physik.rwth-aachen.de>
#
#    This file is part of the Bobcat program.
#
#    Bobcat is free software; you can use it, redistribute it and/or modify it
#    under the terms of the MIT license.
#
#    You should have received a copy of the MIT license with Bobcat.  If not,
#    see <http://bobcat.origo.ethz.ch/wiki/Licence>.
#

from .common import guarded_match, guarded_search, guarded_find, Node

superscripts = {u"⁰": u"0", u"¹": u"1", u"²": u"2", u"³": u"3", u"⁴": u"4",
                u"⁵": u"5", u"⁶": u"6", u"⁷": u"7", u"⁸": u"8", u"⁹": u"9",
                u"⁺": u"+", u"⁻": u"−", u"⁼", u"=", u"⁽": u"(", u"⁾": u")",
                u"ⁱ": u"i", u"ⁿ": u"n"}

subscripts = {u"₀": u"0", u"₁": u"1", u"₂": u"2", u"₃": u"3", u"₄": u"4",
              u"₅": u"5", u"₆": u"6", u"₇": u"7", u"₈": u"8", u"₉": u"9",
              u"₊": u"+", u"₋": u"−", u"₌", u"=", u"₍": u"(", u"₎": u")",
              u"ₐ": u"a", u"ₑ": u"e", u"ₒ": u"o", u"ₓ": u"x", u"ₔ": u"ə"}

opening_braces = u"([{⟨⟦⟪⟬⟮|‖"
closing_braces = u")]}⟩⟧⟫⟭⟯"

breaking_whitespace = u" " + u"".join([unichr(i) for i in range(0x2000, 0x200b)]) + u"\x205f"
nonbreaking_whitespace = u" \x202f"
whitespace = breaking_whitespace + nonbreaking_whitespace


def parse_math_row(parent, text, position, end):
    return guarded_find("}", text, position, end)

class MathEquation(Node):
    def __init__(self, parent):
        super(MathEquation, self).__init__(parent)
    def parse(self, text, position, end):
        super(MathEquation, self).parse(text, position)
        position = parse_math_row(self, text, position, end)
        if position >= len(text) or text[position] != "}":
            self.throw_parse_error("Math equation is not terminated with }")
        return position + 1
