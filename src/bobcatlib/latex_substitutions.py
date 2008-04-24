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

ur"""Find LaTeX representation of Unicode characters.  For example, a δ should
become ``\delta``.  However, the representatoon may depend on the context.
Outside a formula, for example, it must be ``$\delta$``.  Thus, it is a helping
module for the LaTeX backend.


:var cached_substitutions_with_fallbacks: internal dictionary containing
  language substitutions for languages already requested, so that they can be
  delivered faster when requested again.  So the values of this dict are again
  dicts.
:var cached_substitutions: all LaTeX substitutions read so far.  Its keys are
  full language tags.  In contrast to `cached_substitutions_with_fallbacks`,
  this dict contains substitions directly read from bls files, so without any
  fallbacks.  `cached_substitutions_with_fallbacks` merges the substitions sets
  for the complete fallback chain downto English.
:var undangerous_characters: string containing all characters that can be
  copied into the LaTeX file safely under all circumstances, contexts and
  languages.
:var replacement_macro: LaTeX macro for the Unicode replacement character
:var combining_diacritical_marks: list of Unicode characters that are combining
  diacritical marks

:type cached_substitutions_with_fallbacks: dict
:type cached_substitutions: dict
:type undangerous_characters: str
:type replacement_macro: str
:type combining_diacritical_marks: list of unicode
"""

import re, os.path, codecs, string, sys
from . import common
from .common import Error, FileError

class Substitution(object):
    """Basic LaTeX Unicode substitution.  This is just a container for the
    LaTeX replacement and the package needed for it to work.

    :ivar replacement: The LaTeX macro for the Unicode to which this
      substitution belongs.
    :ivar package: The package needed for `replacement` to work.  `None` if the
      substitution works without special packages.
    :cvar packages: set with all packages needed so far.  It is updated with
      every substitution request.

    :type replacement: unicode
    :type package: str
    :type packages: set of str
    """
    def __init__(self, substitution):
        """:Parameters:
          - `substitution`: the LaTeX replacement and the needed package.  The
            latter may be `None`.

        :type substitution: tuple of (unicode, str)
        """
        self.replacement, self.package = substitution
    @classmethod
    def reset_packages(cls, packages):
        """Sets the packages to a given set.

        :Parameters:
          - `packages`: a set of packages which contains the additional
            packages that have been requested so far.  Normally, it contains
            the original `latex.packages` (not a copy of it!).
        """
        cls.packages = packages
    def __unicode__(self):
        u"""Returns the LaTeX replacement of the current Substitution.
        Additionally, it adds the package needed for this substitution – if
        there is one – to `packages`.

        :Return:
          The LaTeX replacement

        :rtype: unicode
        """
        if self.package:
            Substitution.packages.add(self.package)
        return self.replacement

# FixMe: The following path variable will eventually be set by some sort of
# configuration.
latex_substitutions_path = os.path.join(common.modulepath, "data")

def read_latex_substitutions(language_code):
    """Read the LaTeX substitutions from a bls file for one language and return
    the resulting dictionary of language substitutions.

    :Parameters:
      - `language_code`: language code to be read.  This is the file name this
        procedure will look for.  It is the *first* part of the language code
        according to :RFC:`4646`.  Mostly, it is two letters long.

    :type language_code: str

    :Return:
      the substitutions for this language as a dictionary of language_codes
      mapped to dictinaries of characters which are mapped to dictionaries of
      modes mapped to replacements

    :rtype: dict
    """
    substitutions = {}
    language_code = language_code.lower()
    filename = os.path.join(latex_substitutions_path, language_code+".bls")
    local_variables = common.parse_local_variables(open(filename).readline(), force=True)
    file_language_code = local_variables.get("language-code")
    if not file_language_code:
        raise FileError("language code missing in first line", filename)
    file_language_code = file_language_code.lower()
    if file_language_code != language_code:
        raise FileError("language code in first line doesn't match file name", filename)
    latex_substitutions_file = codecs.open(filename, encoding=local_variables.get("coding", "utf8"))
    latex_substitutions_file.readline()
    if not re.match(r"\.\. Bobcat LaTeX substitutions\Z",
                    latex_substitutions_file.readline().rstrip()):
        raise FileError("second line is invalid", filename)
    line_pattern = re.compile(r"((?P<character>.)|(#(?P<dec>\d+))|(0x(?P<hex>[0-9a-fA-F]+)))"
                              r"\t+(?P<replacement>[^\n\r\t]+)(\t+(?P<package>.*))?\Z")
    surrogate_line_pattern = \
        re.compile(r"(?P<characters>.[^\t])\t+(?P<replacement>[^\n\r\t]+)(\t+(?P<package>.*))?\Z")
    mode_line_pattern = re.compile(r"(?P<modes>(TEXT|MATH|SECTION|INDEX|BIBTEX)"
                                   r"([, \t]+(TEXT|MATH|SECTION|INDEX|BIBTEX))*)"
                                   r"(?P<language_codes>"
                                   r"(?:[, \t]+([a-z]{2,3}(?:-[a-zA-Z0-9]+){0,2}))*)\s*\Z")
    modes = language_codes = None
    for i, line in enumerate(latex_substitutions_file):
        linenumber = i + 3
        if line.strip() == "" or line.rstrip() == ".." or line.startswith(".. "):
            continue
        line = line.rstrip("\r\n")
        line_match = line_pattern.match(line)
        if line_match:
            if line_match.group("character"):
                character = line_match.group("character")
            elif line_match.group("dec"):
                character = unichr(int(line_match.group("dec")))
            elif line_match.group("hex"):
                character = unichr(int(line_match.group("hex"), 16))
            if not language_codes:
                raise FileError("mode line expected in line %d" % linenumber, filename)
            for language_code in language_codes:
                if language_code not in substitutions:
                    substitutions[language_code] = {}
                if character not in substitutions[language_code]:
                    substitutions[language_code][character] = {}
                for mode in modes:
                    substitutions[language_code][character][mode] = \
                        Substitution(line_match.group("replacement", "package"))
        else:
            # Mode line?
            line_match = mode_line_pattern.match(line)
            if not line_match:
                # FixMe: The following test will probably work but it is
                # sub-optimal
                if sys.maxunicode > 65535 or not surrogate_line_pattern.match(line):
                    raise FileError("line %d is invalid" % linenumber, filename)
                else:
                    # Surrogate character because Python installation has an
                    # upper limit of 16 bit Unicode characters.  So, simply
                    # ignore the line
                    continue
            modes = line_match.group("modes").replace(",", " ").split()
            language_codes = [code.lower() for code in
                              line_match.group("language_codes").replace(",", " ").split()]
            for lang_code in language_codes:
                if not lang_code.startswith(language_code):
                    raise Error("invalid language code")
            if not language_codes:
                language_codes = [language_code]
    return substitutions

cached_substitutions_with_fallbacks = {}
cached_substitutions = {}
def build_language_substitutions(language_code):
    """Generate the replacement dictionary for one specific language,
    e.g. de-de-1996.  This routine uses fallbacks for languages with shorter
    code, e.g. de-de or de, and for English ("en") as the general fallback.

    :Parameters:
      - `language_code`: language_code accroding to :RFC:`4747`.  This is a
        full language code as found in the Bobcat source file.

    :type language_code: str

    :Return:
      the dictionary of characters mapped to dictionaries of modes mapped to
      LaTeX replacements for this language

    :rtype: dict
    """
    def get_main_code(language_code):
        """Return only the first tag of a full language code."""
        dash_position = language_code.find("-")
        if dash_position == -1:
            return language_code
        return language_code[:dash_position]

    language_code = language_code.lower()
    if language_code in cached_substitutions_with_fallbacks:
        return cached_substitutions_with_fallbacks[language_code]
    main_codes = [get_main_code(lc) for lc in cached_substitutions]
    if "en" not in main_codes:
        cached_substitutions.update(read_latex_substitutions("en"))
    assert "en" in [get_main_code(lc) for lc in cached_substitutions], "en.bls was invalid"
    main_code = get_main_code(language_code)
    if main_code not in main_codes and \
            os.path.isfile(os.path.join(latex_substitutions_path, main_code+".bls")):
        cached_substitutions.update(read_latex_substitutions(main_code))
        assert main_code in [get_main_code(lc) for lc in cached_substitutions], \
            "file %s was invalid, it didn't contain pure '%s' substitutions" % \
            (main_code+".bls", main_code)
    language_substitutions = {}
    language_codes = [lc for lc in cached_substitutions if language_code.startswith(lc)]
    language_codes.sort()
    if "en" not in language_codes:
        language_codes = ["en"] + language_codes
    for lang_code in language_codes:
        language_substitutions.update(cached_substitutions[lang_code])
    cached_substitutions_with_fallbacks[language_code] = language_substitutions
    return language_substitutions

ascii_letters_digits = string.ascii_letters + string.digits + " \t\r\n"
undangerous_characters = ascii_letters_digits + " \t\r\n"
replacement_macro = ur"\replacecharacter{}"
# FixMe: The combining diacritical marks CDM are not yet handled in this
# module.  Eventually, the current character can be identified as a CDM by
# testing membership in one of the two following lists.  Then, it must step
# back in the processed output stream just before the last (or last two)
# characters.  Then, insert the diacritical mark (which always ends in \\ in
# the substitutions file).  For the stepping back, the last two insertion
# positions in the output stream must be saved.
#
# Mathematical accents must be processed in a case structure in the Python
# source because there is no general approach.
combining_diacritical_marks = [unichr(codepoint) for codepoint in
                               range(0x300, 0x35c) + range(0x363, 0x37f) + range(0x20d0, 0x20ef)]
del codepoint

def process_text(text, language, mode, packages=None):
    u"""Takes the unicode string `text` and converts it to a LaTeX string.

    >>> process_text(u"\\u2192", "de", "TEXT")
    u'$\\\\rightarrow${}'

    :Parameters:
      - `text`: The unicode text
      - `language`: current language code accoring to :RFC:`4646`
      - `mode`: One of "TEXT", "MATH", "SECTION", "INDEX", "BIBTEX".  This
        denotes the LaTeX context of `text`.
      - `packages`: A set of strings with all additional packages used so far.
        In order to print exotic characters, special packages may be needed.
        They are added to this set.

    :type text: unicode
    :type language: str
    :type mode: str
    :type packages: set

    :Return:
      the LaTeX counterpart of `text`.  It is guaranteed that this Unicode
      string contains only Latin-1-safe characters.

    :rtype: unicode
    """
    # pylint: disable-msg=C0103
    def get_TEXT_substitution(substitutions, following_character):
        """Assume that you are in LaTeX's text mode (horizontal mode) and
        generate a replacement for it.  `following_character` must be ``None``
        or the empty string of there is no following character."""
        if "TEXT" in substitutions:
            substitution = unicode(substitutions["TEXT"])
            if substitution[-1] == "\\":
                if not following_character:
                    substitution = substitution[:-1] + "{}"
                elif following_character not in " \t\r\n":
                    if following_character in ascii_letters_digits:
                        substitution = substitution[:-1] + " "
                    else:
                        substitution = substitution[:-1]
        elif "MATH" in substitutions:
            substitution = u"$" + unicode(substitutions["MATH"]) + "${}"
        else:
            substitution = replacement_macro
        return substitution
    def get_TEXT_escaping(character):
        """Assume that you are in LaTeX's text mode (horizontal mode) and
        generate a properly escaped character for it."""
        character = unicode(character)
        if character in "!?-'`<>":
            return character + "{}"
        elif character in "$%&{}#":
            return "\\" + character
        elif character in r'"\_^~':
            return ur"{\char%d}" % ord(character)
        elif 32 <= ord(character) <= 127 or character in "\t\r\n" or 161 <= ord(character) <= 255:
            return character
        else:
            return replacement_macro

    Substitution.reset_packages(packages or set())
    language_substitutions = build_language_substitutions(language)
    processed_text = u""
    for i, char in enumerate(text):
        # For the sake of performance, I process the 26 Latin letters and the
        # digits first, without any futher conditional expressions
        if char in undangerous_characters:
            processed_text += char
            continue
        unicode_number = ord(char)
        # Now, if there is a substitution registered for this charaters and
        # this mode, use it.  Additionally, if there is a substitution
        # registeres for any mode for a characters above Latin-1, use it.
        if char in language_substitutions and \
                (unicode_number >= 256 or mode in language_substitutions[char]):
            substitutions = language_substitutions[char]
            following_character = text[i+1:i+2]
            is_whitespace_following = following_character and following_character in " \t\r\n"
            if mode == "TEXT":
                substitution = get_TEXT_substitution(substitutions, following_character)
            elif mode == "MATH":
                if "MATH" in substitutions:
                    substitution = unicode(substitutions["MATH"])
                    if not is_whitespace_following:
                        substitution += " "
                elif "TEXT" in substitutions:
                    substitution = ur"\text{" + unicode(substitutions["MATH"]) + "}"
                else:
                    substitution = replacement_macro
            elif mode == "SECTION":
                if "SECTION" in substitutions:
                    substitution = unicode(substitutions["SECTION"])
                    if not is_whitespace_following:
                        substitution += " "
                else:
                    substitution = get_TEXT_substitution(substitutions, following_character)
                if substitution.startswith("$"):
                    substitution = u"??"
                substitution = ur"\texorpdfstring{%s}{%s}" % (process_text(char, language, "TEXT"),
                                                              substitution)
            elif mode == "INDEX":
                if "INDEX" in substitutions:
                    substitution = unicode(substitutions["INDEX"])
                    if not is_whitespace_following:
                        substitution += " "
                else:
                    substitution = get_TEXT_substitution(substitutions, following_character)
            elif mode == "BIBTEX":
                if "BIBTEX" in substitutions:
                    substitution = unicode(substitutions["BIBTEX"])
                else:
                    substitution = get_TEXT_substitution(substitutions, following_character)
                substitution = u"{" + substitution + "}"
            else:
                raise Error("INTERNAL ERROR: invalid mode %s in line '%s'" % (mode, text))
            processed_text += substitution
            continue
        # Okay this is left: Characters without any registered substitution, and
        # characters of Latin-1 with a substitution in the wrong mode (or none
        # at all)
        if mode == "TEXT" or mode == "SECTION":
            processed_text += get_TEXT_escaping(char)
        elif mode == "MATH":
            if char in "$%&{}#":
                processed_text += "\\" + char
            elif char in r'"\_^~':
                processed_text += ur"{\char%d}" % ord(char)
            elif 32 <= unicode_number <= 127 or char in "\t\r\n" or 161 <= unicode_number <= 255:
                processed_text += char
            else:
                processed_text += replacement_macro
        elif mode == "INDEX":
            # FixMe: At least the exclamation mark must be escaped somehow;
            # maybe other characters doesn't work so easily, too.
            processed_text += get_TEXT_escaping(char)
        elif mode == "BIBTEX":
            # FixMe: At least the double quotes must be escaped somehow; maybe
            # other characters doesn't work so easily, too.
            processed_text += get_TEXT_escaping(char)
    return processed_text
