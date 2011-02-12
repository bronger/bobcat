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
import re

superscripts = {u"⁰": u"0", u"¹": u"1", u"²": u"2", u"³": u"3", u"⁴": u"4",
                u"⁵": u"5", u"⁶": u"6", u"⁷": u"7", u"⁸": u"8", u"⁹": u"9",
                u"⁺": u"+", u"⁻": u"−", u"⁼", u"=", u"⁽": u"(", u"⁾": u")",
                u"ⁱ": u"i", u"ⁿ": u"n"}

subscripts = {u"₀": u"0", u"₁": u"1", u"₂": u"2", u"₃": u"3", u"₄": u"4",
              u"₅": u"5", u"₆": u"6", u"₇": u"7", u"₈": u"8", u"₉": u"9",
              u"₊": u"+", u"₋": u"−", u"₌", u"=", u"₍": u"(", u"₎": u")",
              u"ₐ": u"a", u"ₑ": u"e", u"ₒ": u"o", u"ₓ": u"x", u"ₔ": u"ə"}

opening_braces = set(u"([{⟨⟦⟪⟬⟮|‖")
closing_braces = set(u")]}⟩⟧⟫⟭⟯")

relational_operators = set(u"<=>"
                           + u"∴∵∻∼∽∾"
                           + u"≁≂≃≄≅≆≇≈≉≊≋≌≍≎≏≐≑≒≓≔≕≖≗≘≙≚≛≜≝≞≟≠≡≢≣≤≥≦≧≨≩≪≫≬≭≮≯≰≱≲≳≴≵≶≷≸≹≺≻≼≽≾≿⊀⊁⊂⊃⊄⊅⊆⊇⊈⊉⊊⊋"
                           + u"⊏⊐⊑⊒"
                           + u"⊦⊧⊨⊩⊪⊫⊬⊭⊮⊯⊰⊱⊲⊳⊴⊵⊶⊷⊸⊹"
                           + u"⋈⋍"
                           + u"⋔⋕⋖⋗⋘⋙⋚⋛⋜⋝⋞⋟⋠⋡⋢⋣⋤⋥⋦⋧⋨⋩⋪⋫⋬⋭⋮⋯⋰⋱⋲⋳⋴⋵⋶⋷⋸⋹⋺⋻⋼⋽⋾⋿"
                           + u"⧣⧤⧥⧦"
                           + u"⩦⩧⩨⩩⩪⩫⩬⩭⩮⩯⩰⩱⩲⩳⩴⩵⩶⩷⩸⩹⩺⩻⩼⩽⩾⩿⪀⪁⪂⪃⪄⪅⪆⪇⪈⪉⪊⪋⪌⪍⪎⪏⪐⪑⪒⪓⪔⪕⪖⪗⪘⪙⪚⪛⪜⪝⪞⪟⪠⪡⪢⪣⪤⪥⪦⪧⪨⪩⪪⪫⪬⪭"
                           u"⪮⪯⪰⪱⪲⪳⪴⪵⪶⪷⪸⪹⪺⪻⪼⪽⪾⪿⫀⫁⫂⫃⫄⫅⫆⫇⫈⫉⫊⫋⫌⫍⫎⫏⫐⫑⫒⫓⫔⫕⫖⫗⫘⫙⫚⫛⫝̸⫝"
                           + u"⫷⫸⫹⫺⫻")
arrows = set(u"←↑→↓↔↕↖↗↘↙↚↛↜↝↞↟↠↡↢↣↤↥↦↧↨↩↪↫↬↭↮↯↰↱↲↳↴↵↶↷↸↹↺↻↼↽↾↿⇀⇁⇂⇃⇄⇅⇆⇇⇈⇉⇊⇋⇌⇍⇎⇏⇐⇑⇒⇓⇔⇕⇖⇗⇘⇙⇚⇛⇜⇝⇞⇟⇠⇡⇢⇣⇤⇥⇦⇧⇨⇩⇪⇫⇬⇭⇮⇯⇰⇱⇲"
             u"⇳⇴⇵⇶⇷⇸⇹⇺⇻⇼⇽⇾⇿"
             + u"⟰⟱⟲⟳⟴⟵⟶⟷⟸⟹⟺⟻⟼⟽⟾⟿"
             + u"⤀⤁⤂⤃⤄⤅⤆⤇⤈⤉⤊⤋⤌⤍⤎⤏⤐⤑⤒⤓⤔⤕⤖⤗⤘⤙⤚⤛⤜⤝⤞⤟⤠⤡⤢⤣⤤⤥⤦⤧⤨⤩⤪⤫⤬⤭⤮⤯⤰⤱⤲⤳⤴⤵⤶⤷⤸⤹⤺⤻⤼⤽⤾⤿⥀⥁"
             u"⥂⥃⥄⥅⥆⥇⥈⥉⥊⥋⥌⥍⥎⥏⥐⥑⥒⥓⥔⥕⥖⥗⥘⥙⥚⥛⥜⥝⥞⥟⥠⥡⥢⥣⥤⥥⥦⥧⥨⥩⥪⥫⥬⥭⥮⥯⥰⥱⥲⥳⥴⥵⥶⥷⥸⥹⥺⥻⥼⥽⥾⥿"
             + u"⬀⬁⬂⬃⬄⬅⬆⬇⬈⬉⬊⬋⬌⬍⬎⬏⬐⬑"
             + u"⬰⬱⬲⬳⬴⬵⬶⬷⬸⬹⬺⬻⬼⬽⬾⬿⭀⭁⭂⭃⭄⭅⭆⭇⭈⭉⭊⭋⭌")
relational_and_arrows = relational_operators | arrows

breaking_whitespace = set(u" " + u"".join([unichr(i) for i in range(0x2000, 0x200b)]) + u"\x205f")
nonbreaking_whitespace = set(u" \x202f")
whitespace = breaking_whitespace | nonbreaking_whitespace

big_operators = set(u"∏∐∑⋀⋁⋂⋃" + u"⨀⨁⨂⨃⨄⨅⨆⨇⨈⨉⨊⨋⨌⨍⨎⨏⨐⨑⨒⨓⨔⨕⨖⨗⨘⨙⨚⨛⨜⨝⨞⨟⨠⨡")

def is_letter(character):
    return unicodedata.category(character) in ["Lu", "Ll", "Lo", "Lt"]

number_pattern = None
def set_decimal_point(character):
    global number_pattern
    assert character in [u",", u"."]
    number_pattern = re.compile(u"(+|−|-)?[0-9]+({0}[0-9]+)?(e(+|−|-)?[0-9]+)?".format(re.escape(character)))
set_decimal_point(u".")

def parse_math_row(parent, text, position, end):
    return guarded_find("}", text, position, end)

class IdentifierSet(object):
    whitespace_re = u"[{0}]+".format(re.escape(u"".join(whitespace)))
    def __init__(self, identifiers=()):
        self.identifiers = set(identifiers)
    def add(self, identifier):
        """The identifier must be whitespace-normalised!"""
        self.identifiers.add(identifier)
        self.pattern = None
    def match(self, excerpts, pos=0):
        if not self.pattern:
            regular_expression = u"|".join(re.escape(self.identifiers))
            regular_expression.replace(u" ", whitespace_re)
            self.pattern = re.compile(regular_expression, re.UNICODE)
        return self.pattern.match(unicode(excerpt), pos)
builtin_functions = IdentifierSet(
    u"sin", u"cos", u"tan", u"cot", u"sec", u"csc", u"arcsin", u"arccos", u"arctan", u"arccot",
    u"arcsec", u"arccsc", u"sinh", u"cosh", u"tanh", u"coth", u"arg", u"deg", u"dim", u"exp",
    u"lg", u"ln", u"log", u"mod", u"hom", u"ker", u"sgn")
builtin_big_identifiers = IdentifierSet(
    u"lim inf", u"lim sup", u"max", u"min", u"inf", u"sup", u"Pr", u"gcd", u"det", u"lim")
builtin_identifiers = IdentifierSet()

class MathEquation(Node):
    def __init__(self, parent):
        super(MathEquation, self).__init__(parent)
    def parse(self, text, position, end):
        super(MathEquation, self).parse(text, position)
        position = parse_math_row(self, text, position, end)
        if position >= len(text) or text[position] != "}":
            self.throw_parse_error("Math equation is not terminated with }")
        return position + 1
