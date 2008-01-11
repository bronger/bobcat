#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright © 2007 Torsten Bronger <bronger@physik.rwth-aachen.de>
#
#    This file is part of the Gummi program.
#
#    Gummi is free software; you can redistribute it and/or modify it under
#    the terms of the MIT licence:
#
#    Permission is hereby granted, free of charge, to any person obtaining a
#    copy of this software and associated documentation files (the "Software"),
#    to deal in the Software without restriction, including without limitation
#    the rights to use, copy, modify, merge, publish, distribute, sublicense,
#    and/or sell copies of the Software, and to permit persons to whom the
#    Software is furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in
#    all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#

"""The preprocessor of Gummi source files.

Its main purpose is twofold: First, it converts characters sequences to single
Unicode characters.  And secondly, it keeps track of the origins of the
preprocessed text, so that in case of parsing errors the user can be told where
exactly the error occured in the source document.

It achieves this by one fat unicode-like data type called `Excerpt`.
"""

import re, os.path, codecs, string, sys, warnings
import common
from common import Error, FileError, LocalVariablesError, EncodingError

class Excerpt(unicode):
    """Class for preprocessed Gummi source text. It behaves like a unicode string
    with extra methods and attributes.

    The typical lifecycle of such an object is as follows:

    1. The Gummi source text is read from the file (or whereever) and stored as
       one big unicode string.

    2. This unicode string is used to create an Excerpt instance from it.  In
       order to do this, the pre input method rules are applied.

    3. This excerpt is send to the parser that divides it into smaller and
       smaller excerpts, parsing it recursively while building the parse tree.

    4. When parsing is finished, the post input method is applied (which is
       usually *much* smaller than the pre method).

    5. Now, the excerpts are given to the routines of the backend, which
       process them further, convert them to unicodes, and write them to the
       output.

    :cvar entity_pattern: Regexp pattern for numerical entities like
      ``\\0x0207;`` or ``\\#8022;``.
    :type entity_pattern: re.pattern
    """
    # FixMe: The following pylint directive is necessary because astng doesn't
    # parse attribute settings in the __new__ classmethod.  If this changes or
    # if a workaround is found, this directive should be removed in order to
    # find real errors.
    #
    # pylint: disable-msg=E1101
    entity_pattern = re.compile(r"((0x(?P<hex>[0-9a-fA-F]+))|(#(?P<dec>[0-9]+)));")
    @classmethod
    def get_next_match(cls, original_text, substitutions, offset=0):
        """Return the next input method match in `original_text`.  The search
        starts at `offset`.

        :Parameters:
          - `original_text`: the original line in the Gummi input file
          - `substitutions`: the substitution dictionary to be used
          - `offset`: starting position for the search in original_text

        :type original_text: unicode
        :type substitutions: list with the (match, replacement) tuples
        :type offset: int

        :Return:
          the position of the found match, the length of the match, and the
          replacement for this match (a single character).  If no match was
          found, it's len(original_text), 0, None instead

        :rtype: int, int, unicode
        """
        earliest_match_position = len(original_text)
        longest_match_length = 0
        best_match = None
        for substitution in substitutions:
            match = substitution[0].search(original_text, offset)
            if match and match.group().count("\r") + match.group().count("\n") == 0:
                start, end = match.span()
                if start == earliest_match_position:
                    if end - start > longest_match_length:
                        longest_match_length = end - start
                        best_match = match
                        replacement = substitution[1]
                elif start < earliest_match_position:
                    earliest_match_position = start
                    longest_match_length = end - start
                    best_match = match
                    replacement = substitution[1]
        if not best_match or not best_match.group():
            return len(original_text), 0, None
        return best_match.start(), best_match.end() - best_match.start(), replacement
    class PositionMarker(object):
        """A mere container for a position in the original unicode string.

        This would be a struct in C and a record in Pascal.

        :ivar url: URL of the file from which this position comes
        :ivar linenumber: linenumber (starting with 1) of the line from which
          this position comes
        :ivar column: column (starting with 0) within the file where this
          position is found
        :ivar index: index within original_text of the Excerpt this
          PositionMarker belongs to where this position is found

        :type url: str
        :type linenumber: int
        :type column: int
        :type index: int
        """
        def __init__(self, url, linenumber, column, index):
            self.url = url
            self.linenumber = linenumber
            self.column = column
            self.index = index
        def __repr__(self):
            return 'Excerpt.PositionMarker("%s", %d, %d, %d)' % \
                (self.url, self.linenumber, self.column, self.index)
        def __cmp__(self, other):
            """The `index` must not be included in the decision whether two PositionMarkers
            are the same."""
            return cmp((self.url, self.linenumber, self.column),
                       (other.url, other.linenumber, other.column))
        def transpose(self, offset):
            """Return a new PositionMarker instance in order to get rid of side
            effect problems, by forcing making a *copy*.  Additionally, index
            is adjusted by `offset`, which is used in the slicing, indexing and
            concatenation routines of Excerpt.

            :Parameters:
              - `offset`: the offset that is added to the index attribute of
                the generated PositionMarker instance.  May be positive or
                negative or zero.

            :type offset: int

            :Return:
              a newly created PositionMarker instance

            :rtype: PositionMarker
            """
            return Excerpt.PositionMarker(self.url, self.linenumber, self.column,
                                          self.index+offset)
    def is_escaped(self, position):
        """Return True, if the character at position is escaped.

        :Parameters:
          - `position`: the position or interval in the Excerpt

        :type position: int or (int, int)

        :Return:
          whether or not the character at `position` is escaped.  If an
          interval was given, whether or not at least one character in the
          interval is escaped.

        :rtype: boolean
        """
        # Note that self.escaped_positions must be sorted!
        if isinstance(position, (list, tuple)):
            a, b = position
            for i in self.escaped_positions:
                if a <= i < b:
                    return True
            return False
        else:
            return position in self.escaped_positions
    def next_escaped_position(self, offset):
        length = len(self)
        if offset >= length:
            raise IndexError("invalid value %d for "
                        "offset in next_escaped_position near line %d of file %s" %
                        (offset, self.original_positions[0].linenumber, self.original_positions[0].url))
        next_positions = [position for position in self.escaped_positions if position >= offset]
        if next_positions:
            return sorted(next_positions)[0]
        else:
            return len(self)
    def escaped_text(self):
        """Returns the unicode representation of the Excerpt with all escaped
        characters replaced with Null characters.

        :Return:
          the unicode representation of the Excerpt with all escaped characters
          replaced with Null characters

        :rtype: unicode
        """
        # pylint: disable-msg=E0203
        if self.__escaped_text is None:
            text = list(unicode(self))
            for pos in self.escaped_positions:
                text[pos] = u"\u0000"
            self.__escaped_text = u"".join(text)
        return self.__escaped_text
    def original_position(self, position):
        """Maps a position within the excerpt to the position in the original
        file.

        :Parameters:
          - `position`: the position in the excerpt to which this method
            belongs. Note that len(self) is an allowed value for `position`, in
            order to get the original span of the whole string.

        :type position: int

        :Return:
          the Position the given character originates from.  This includes url
          (filename), linenumber, and column.  None if the Excerpt is empty.

        :rtype: PositionMarker

        :Exceptions:
          - `IndexError`: if a position was requested which lies outside the
            line.
        """
        length = len(self)
        if not 0 <= position <= length:
            raise IndexError("invalid value %d for "
                        "position in original_position near line %d of file %s" %
                        (position, self.original_positions[0].linenumber, self.original_positions[0].url))
        if length == 0:
            return None
        closest_position = max([pos for pos in self.original_positions if pos <= position])
        offset = position - closest_position
        closest_marker = self.original_positions[closest_position].transpose(offset)
        closest_marker.column += offset
        return closest_marker
    class Status(object):
        """A mere container for some immutable data structures used in the pre-
        and postprocessing.

        The only reason for its existence is that the "nonlocal" statement is
        not yet implemented in Python.  Therefore, I need a mutable data type
        in order to use side effects in the local functions in
        apply_pre_input_method() and apply_post_input_method().  It's not nice,
        but the alternatives are even uglier.  BTDT.

        Tu sum it up, Status holds (part of) the current status of the
        pre/postprocessor.

        :ivar linenumber: current linenumber in the source file
        :ivar last_linestart: position of the last character that startet a
          line
        :ivar position: current position in the source file
        :ivar processed_text: the so far already preprocessed text
        :ivar in_sourcecode: are we in source code enclosed by tripple
          backquotes?

        :type linenumber: int
        :type last_linestart: int
        :type position: int
        :type processed_text: unicode
        :type in_sourcecode: bool
        """
        def __init__(self):
            self.linenumber = 0
            self.last_linestart = 0
            self.position = 0
            self.processed_text = u""
            self.in_sourcecode = False
    @classmethod
    def apply_pre_input_method(cls, original_text, url, pre_substitutions):
        """This class method transforms the pristine line `original_text` into
        a processed line, escpecially by applying substitutions by the pre(!)
        input method.

        :Parameters:
          - `original_text`: the original text from a Gummi source file
          - `url`: URL of the original ressource file
          - `pre_substitutions`: substitution list of the pre input method

        :type original_text: unicode
        :type url: str
        :type pre_substitutions: list with the (match, replacement) tuples

        :Return:
          - the processed line
          - original positions as a dict of position -- (filename, linenumber,
            column).  The linenumber starts at 1, the column at 0.
          - positions of escaped characters as a list of positions

        :rtype: unicode, dict, list
        """
        comment_line_pattern = re.compile(r"^\.\.( .*)?$", re.MULTILINE)
        # The following functions seem to violate an important programming
        # rule: They modify variables of the outer scope, i.e. the enclosing
        # function (side effects).  However, they are simple to explain and
        # they do simple things, so this approach leads to easy-to-comprehend
        # code.  Therefore, I make an exception to that rule.
        def drop_characters(number_of_characters):
            """This routine must be called immediately after the character is
            being added to `preprocessed_text` and the current `position`
            points to the next character in `original_text` to be processed.
            Thus, this is a mere synchronisation between `original_text` and
            `preprocessed_text`.
            """
            s.position += number_of_characters
            # Now re-sync
            original_positions[len(s.processed_text)] = \
                Excerpt.PositionMarker(url, s.linenumber,
                                       s.position - s.last_linestart, s.position)
        def escape_next_character():
            escaped_positions.add(len(s.processed_text))
        def copy_character(char=None):
            """Beware: It is only allowed that `char` is one single
            character. In particular, s.processed_text must consist only of
            single characters, otherwise len(s.processed_text) would yield a
            wrong string length!
            """
            if char == None:
                char = current_char
            s.processed_text.append(char)
            s.position += 1
        def resync_at_linestart():
            s.linenumber += 1
            s.last_linestart = s.position
            comment_match = comment_line_pattern.match(original_text, s.position)
            if comment_match:
                # Drop comment lines
                drop_characters(comment_match.end() - comment_match.start())
            else:
                drop_characters(0)

        s = Excerpt.Status()
        # For performance reasons, I use a list of unicode strings rather than
        # a unicode string for the result string.  Before returning it, I will
        # concetenate all list elements to one string.  This is really much
        # faster for strings longer than a couple of 10k.
        s.processed_text = []
        original_positions = {}
        escaped_positions = set()
        deferred_escape = False
        resync_at_linestart()
        # For the sake of performance, I don't test every characters position
        # for input method matches, but look for the next upcoming match and
        # store it.
        next_match_position, next_match_length, replacement = \
            cls.get_next_match(original_text, pre_substitutions)
        # Next comes the Big While which crawls through the whole source code
        # and preprocesses it.
        while s.position < len(original_text):
            current_char = original_text[s.position]
            if current_char in string.whitespace:
                if deferred_escape and current_char in " \t":
                    # drop the tab or space
                    drop_characters(1)
                elif current_char in "\n\r":
                    if original_text[s.last_linestart:s.position].strip() == "":
                        deferred_escape = False
                    # Here, I normalize all line endings to "\n".  In order to
                    # avoid generating a new position marker, I convert \r if
                    # followed by a \n to a space (so this may generate
                    # trailing spaces).
                    if current_char == "\r" and original_text[s.position+1:s.position+2] == "\n":
                        copy_character(" ")
                    copy_character("\n")
                    # For performance, make a sync at every linestart
                    resync_at_linestart()
                else:
                    copy_character()
                continue
            if s.in_sourcecode:
                if original_text[s.position:s.position+3] == "```":
                    copy_character()
                    copy_character()
                    copy_character()
                    s.in_sourcecode = False
                elif original_text[s.position:s.position+2] == r"\`":
                    drop_characters(2)
                    next_character = original_text[s.position+2:s.position+3]
                    if next_character:
                        escape_next_character()
                        copy_character(next_character)
                else:
                    copy_character()
                continue
            if current_char == "\\":
                if original_text[s.position+1:s.position+2] == "\\":
                    if deferred_escape:
                        escape_next_character()
                        deferred_escape = False
                    copy_character()
                    drop_characters(1)
                    deferred_escape = False
                    continue
                entity_match = cls.entity_pattern.match(original_text, s.position+1)
                if entity_match:
                    if entity_match.group("hex"):
                        char = unichr(int(entity_match.group("hex"), 16))
                    elif entity_match.group("dec"):
                        char = unichr(int(entity_match.group("dec")))
                    if deferred_escape:
                        escape_next_character()
                        deferred_escape = False
                    copy_character(char)
                    drop_characters(entity_match.end() - entity_match.start())
                    continue
            if (current_char == "[" and original_text[s.position+1:s.position+2] == "[") or \
                    (current_char == "]" and original_text[s.position+1:s.position+2] == "]"):
                escape_next_character()
                copy_character()
                drop_characters(1)
                deferred_escape = False
                continue
            if s.position > next_match_position:
                # I must update the next match
                next_match_position, next_match_length, replacement = \
                    cls.get_next_match(original_text, pre_substitutions, s.position)
            if s.position == next_match_position:
                if deferred_escape:
                    escape_next_character()
                copy_character(replacement)
                drop_characters(next_match_length - 1)
                deferred_escape = False
                continue
            if current_char == "\\":
                deferred_escape = False
                next_character = original_text[s.position+1:s.position+2]
                if s.position + 1 == next_match_position:
                    drop_characters(1)
                    copy_character(next_character)
                elif next_character and (next_character not in string.whitespace):
                    escape_next_character()
                    drop_characters(1)
                    copy_character(next_character)
                else:
                    drop_characters(1)
                    deferred_escape = True
                continue
            if current_char == "`" and original_text[s.position+1:s.position+3] == "``" \
                    and not deferred_escape:
                s.in_sourcecode = True
                copy_character()
                copy_character()
                copy_character()
                continue
            # Now for the usual case of an ordinary character
            if deferred_escape:
                escape_next_character()
                deferred_escape = False
            copy_character()
        return u"".join(s.processed_text), original_positions, escaped_positions
    def __add__(self, other):
        if not isinstance(other, Excerpt):
            return NotImplemented
        concatenation = unicode(self) + unicode(other)
        concatenation = Excerpt(concatenation, mode="NONE")
        assert self.post_substitutions == other.post_substitutions
        concatenation.post_substitutions = self.post_substitutions
        concatenation.original_text = self.original_text + other.original_text
        concatenation.original_positions = self.original_positions.copy()
        length_first_part = len(self)
        length_first_part_original = len(self.original_text)
        concatenation.original_positions.update\
            ([(pos + length_first_part, other.original_positions[pos].transpose(length_first_part_original))
              for pos in other.original_positions if pos > 0])
        first_mark_in_second_excerpt = other.original_positions[0]
        if self.original_position(length_first_part) != first_mark_in_second_excerpt:
            # Should be necessary almost always, but here we go
            concatenation.original_positions[length_first_part] = \
                first_mark_in_second_excerpt.transpose(length_first_part_original)
        concatenation.escaped_positions = self.escaped_positions | \
            set([pos + length_first_part for pos in other.escaped_positions])
        return concatenation
    def __getitem__(self, key):
        if key < 0:
            key += len(self)
        character = super(Excerpt, self).__getitem__(key)
        character = Excerpt(character, mode="NONE")
        character.post_substitutions = self.post_substitutions
        marker = self.original_positions.get(key, self.original_position(key))
        character.original_text = self.original_text[marker.index:self.original_position(key+1).index]
        marker.index = 0
        character.original_positions = {0: marker}
        if key in self.escaped_positions:
            character.escaped_positions = set([0])
        else:
            character.escaped_positions = set()
        return character
    def __getslice__(self, i, j):
        length = len(self)
        i = max(min(i, length), 0)
        j = max(min(j, length), i)
        text = super(Excerpt, self).__getslice__(i, j)
        slice = Excerpt(text, mode="NONE")
        slice.post_substitutions = self.post_substitutions
        start_marker = self.original_position(i)
        offset = start_marker.index
        slice.original_text = self.original_text[start_marker.index:self.original_position(j).index]
        slice.original_positions = \
            dict([(pos - i, self.original_positions[pos].transpose(-offset))
                  for pos in self.original_positions if i <= pos < j])
        if 0 not in slice.original_positions:
            slice.original_positions[0] = start_marker.transpose(-offset)
        slice.escaped_positions = set([pos - i for pos in self.escaped_positions if i <= pos < j])
        return slice
    @classmethod
    def apply_post_input_method(cls, excerpt):
        """This class method transforms an excerpt into a terminally processed text by
        applying substitutions by the post input method.  This means that this
        text has already been preprocessed and parsed.  It is in a terminal
        text node, and post-processing is the final step before the backend
        sees it.

        :Parameters:
          - `excerpt`: the original excerpt

        :type excerpt: Excerpt

        :Return:
          - the processed text
          - original positions as a dict of position -- (filename, linenumber,
            column).  The linenumber starts at 1, the column at 0.
          - positions of escaped characters as a list of positions

        :rtype: unicode, dict, list
        """
        # The following functions seem to violate an important programming
        # rule: They modify variables of the outer scope, i.e. the enclosing
        # function (side effects).  However, they are simple to explain and
        # they do simple things, so this approach leads to easy-to-comprehend
        # code.  Therefore, I make an exception to that rule.
        #
        # Their semantics are taken from those in apply_pre_input_method(),
        # however, their implementation differs a little bit.
        def drop_characters(number_of_characters):
            """This routine must be called immediately after the character is
            being added to `preprocessed_text` and the current `position`
            points to the next character in `original_text` to be processed.
            """
            s.position += number_of_characters
            if s.position not in excerpt.original_positions:
                original_positions[len(s.processed_text)] = excerpt.original_position(s.position)
        def copy_character(char=None):
            if char == None:
                char = current_char
            s.processed_text += char
            s.position += 1

        s = Excerpt.Status()
        original_positions = {}
        escaped_positions = set()
        # For the sake of performance, I don't test every characters position
        # for input method matches, but look for the next upcoming match and
        # store it.
        text = unicode(excerpt)
        next_match_position, next_match_length, replacement = \
            cls.get_next_match(text, excerpt.post_substitutions)
        # Next comes the Big While which crawls through the whole source code
        # and postprocesses it.
        while s.position < len(text):
            if s.position in excerpt.escaped_positions:
                escaped_positions.add(len(s.processed_text))
            if s.position in excerpt.original_positions:
                original_positions[len(s.processed_text)] = excerpt.original_positions[s.position]
            current_char = text[s.position]
            if current_char in string.whitespace:
                copy_character()
                continue
            if s.position > next_match_position:
                # I must update the next match
                next_match_position, next_match_length, replacement = \
                    cls.get_next_match(text, excerpt.post_substitutions, s.position)
            if s.position == next_match_position:
                any_escaped = False
                for i in range(s.position, s.position + next_match_length):
                    if i in excerpt.escaped_positions:
                        any_escaped = True
                        break
                if not any_escaped:
                    copy_character(replacement)
                    drop_characters(next_match_length - 1)
                    continue
            # Now for the usual case of an ordinary character
            copy_character()
        return s.processed_text, original_positions, escaped_positions
    def __new__(cls, excerpt, mode, url=None,
                pre_substitutions=None, post_substitutions=None):
        """Here I create the instance.  I create a unicode object and add some
        attributes to it.  Note that this class doesn't have an __init__
        method.  There are three "modes", reflecting the three stages in the
        lifecycle of an Excerpt.  Note that the mode "NONE" is used for slicing
        and indexing.

        :Parameters:
          - `excerpt`: the original text that will be used for initialising the
            instance.  If mode is "PRE" or "NONE", this should be a unicode
            string, else it must be an Excerpt itself.
          - `mode`: Either "PRE", "POST", or "NONE".  This tells the method
            which input must be applied (if at all), and of what type is
            `excerpt`.  (See above.)
          - `url`: URL of the original ressource file.  Must be given only for
            the "PRE" mode.
          - `pre_substitutions`: substitution list of the pre input method.
            Must be given only for the "PRE" mode.
          - `post_substitutions`: substitution list of the post input method.
            Must be given only for the "PRE" mode.

        :type excerpt: unicode or Excerpt
        :type mode: str
        :type url: str
        :type pre_substitutions: list with the (match, replacement) tuples
        :type post_substitutions: list with the (match, replacement) tuples

        :Return:
          the newly created instance of Excerpt.

        :rtype: Excerpt
        """
        if mode == "NONE":
            self = unicode.__new__(cls, excerpt)
        elif mode == "PRE":
            preprocessed_text, original_positions, escaped_positions = \
                cls.apply_pre_input_method(excerpt, url, pre_substitutions)
            self = unicode.__new__(cls, preprocessed_text)
            self.original_text = unicode(excerpt)
            self.original_positions = original_positions
            self.escaped_positions = escaped_positions
            self.post_substitutions = post_substitutions
        elif mode == "POST":
            postprocessed_text, original_positions, escaped_positions = \
                cls.apply_post_input_method(excerpt)
            self = unicode.__new__(cls, postprocessed_text)
            self.original_positions = original_positions
            self.escaped_positions = escaped_positions
            self.original_text = excerpt.original_text
            self.post_substitutions = post_substitutions
        self.__escaped_text = None
        return self
    def apply_postprocessing(self):
        """Applies the rules for post processing this the excerpt and returns
        the processed excerpt.  Note that this method can be called only once
        per excerpt, i.e., for the returned excerpt, this method cannot be
        called once again.

        :Return:
          the newly created instance of Excerpt, with applied post input
          method.

        :rtype: Excerpt
        """
        return Excerpt(self, mode="POST")

# FixMe: The following path variable will eventually be set by some sort of
# configuration.
input_methods_path = common.modulepath

def read_input_method(input_method_name):
    """Return the substitution dictionary for one input method.

    :Parameters:
      - `input_method_name`: name of the input method, e.g. "minimal"

    :type input_method_name: string

    :Return:
      A list with the (match, replacement) tuples.  Both are strings, the first
      being a regular expression, and the second one single character. Their
      order is the same as in the file, and duplicates are not deleted.

    :rtype: list

    :Exceptions:
      - `LocalVariablesError`: if the first line is not a local variables line
      - `FileError`: if there is an invalid line in the file
    """
    if input_method_name == "none":
        return [], []
    pre_substitutions = []
    post_substitutions = []
    filename = os.path.join(input_methods_path, input_method_name+".gim")
    local_variables = common.parse_local_variables(open(filename).readline(), force=True)
    if local_variables.get("input-method-name") != input_method_name:
        raise FileError("input method name in first line doesn't match file name", filename)
    input_method_file = codecs.open(filename, encoding=local_variables.get("coding", "utf8"))
    input_method_file.readline()
    if not re.match(r"\.\. Gummi input method\Z", input_method_file.readline().rstrip()):
        raise FileError("second line is invalid", filename)
    if "parental-input-method" in local_variables:
        for input_method in local_variables["parental-input-method"].split(","):
            parent_pre, parent_post = read_input_method(input_method)
            pre_substitutions.extend(parent_pre)
            post_substitutions.extend(parent_post)
    line_pattern = re.compile(r"(?P<match>.+?)\t+"
                              r"((?P<replacement>.)|(#(?P<dec>\d+))|(0x(?P<hex>[0-9a-fA-F]+)))"
                              r"(\s+.*\s*)?\Z")
    for i, line in enumerate(input_method_file):
        linenumber = i + 3
        if line.strip() == "" or line.rstrip() == ".."  or line.startswith(".. "):
            continue
        line_match = line_pattern.match(line)
        if not line_match:
            raise FileError("line %d is invalid" % linenumber, filename)
        match = line_match.group("match")
        post = match.startswith("POST::")
        if post:
            match = match[6:]
        if match.startswith("REGEX::"):
            match = match[7:]
            if re.match(u"(?:"+match+u")?", "").groups():
                raise FileError("the match in line %d contains a group" % linenumber, filename)
        else:
            match = re.escape(match)
        if line_match.group("replacement"):
            replacement = line_match.group("replacement")
        elif line_match.group("dec"):
            replacement = unichr(int(line_match.group("dec")))
        elif line_match.group("hex"):
            replacement = unichr(int(line_match.group("hex"), 16))
        if post:
            post_substitutions.append((match, replacement))
        else:
            pre_substitutions.append((match, replacement))
    return pre_substitutions, post_substitutions

def process_text(text, filepath, input_method):
    """Take the raw contents of the Gummi file and turn it into "digested"
    contents with applied input method and marking of escaped characters.

    :Parameters:
      - `text`: raw contents of the input file.  Only the encoding was
        applied.
      - `filepath`: path to the Gummi input file.  This is only used for the
        error messages.
      - `input_method`: name of the input method to be applied.  If more than
        one, a list of names of input methods.

    :type text: unicode
    :type filepath: string
    :type input_method: string or list of strings

    :Return:
      the preprocessed contents

    :rtype: Excerpt
    """
    def sort_and_filter_substitutions(substitutions):
        # Next, sort and filter the list of substitutions: Reverse order, and
        # remove duplicates.  Additionally, complile the regular expressions to
        # match objects.
        hitherto_matches = set()
        sorted_substitutions = []
        for i in range(len(substitutions)):
            match, replacement = substitutions[-i-1]
            if match not in hitherto_matches:
                hitherto_matches.add(match)
                sorted_substitutions.append((re.compile(match, re.MULTILINE), replacement))
        return sorted_substitutions
    
    # First, read the input method(s)
    if isinstance(input_method, list):
        input_methods = input_method
    else:
        input_methods = [input_method]
    pre_substitutions = []
    post_substitutions = []
    for input_method in input_methods:
        pre, post = read_input_method(input_method)
        pre_substitutions.extend(pre)
        post_substitutions.extend(post)
    pre_substitutions = sort_and_filter_substitutions(pre_substitutions)
    post_substitutions = sort_and_filter_substitutions(post_substitutions)
    # Now, apply it to the contents
    return Excerpt(text, "PRE", filepath, pre_substitutions, post_substitutions)

def detect_header_data(file):
    """Detect the local variables of the given text file and the Gummi format
    version according to its first two lines.  This is very similar to the
    method used for Python source files.  There is no default encoding, the
    default input method is "minimal".

    :Parameters:
      - `file`: source file, with the file pointer set to the start

    :type file: string

    :Return:
      - encoding of the file.  If none was found, it returns None.
      - input method of the file.  It defaults to "minimal".  If more than one
        input method was given, a list of strings is returned.
      - Gummi version; defaults to "1.0"

    :rtype: string, string, string
    """
    first_line = file.readline()
    local_variables = common.parse_local_variables(first_line)
    if local_variables != None:
        coding = local_variables.get("coding")
        input_method = local_variables.get("input-method", "minimal")
        second_line = file.readline()
    else:
        coding, input_method = None, "minimal"
        second_line = first_line
    if re.match(r"\.\. \s*Gummi", second_line):
        gummi_version_match = re.match(r"\.\. \s*Gummi\s+([0-9]+\.[0-9]+)\s*\Z", second_line)
        if gummi_version_match:
            gummi_version = gummi_version_match.group(1)
        else:
            raise FileError("Gummi version line was invalid", file.name)
    else:
        warnings.warn("No Gummi version was specified.  I assume 1.0.")
        gummi_version = "1.0"
    return coding, input_method, gummi_version

def load_file(filename):
    """Load the Gummi file "filename" and return an `Excerpt` instance containing
    that file.

    :Parameters:
      - `filename`: Gummi filename

    :type filename: string

    :Return:
      - `Excerpt` with the contents of the file
      - auto-detected encoding of the file.  None if the encoding was given
        explicitly in the file.
      - Gummi version of the file as a string

    :rtype: Excerpt, string, string
    """
    encoding, input_method, gummi_version = detect_header_data(open(filename))
    # First, auto-detect encoding
    if encoding:
        try:
            lines = codecs.open(filename, encoding=encoding).readlines()
            encoding = None
        except UnicodeDecodeError:
            raise EncodingError("The encoding given in the file (%s) was wrong." % encoding,
                                filename)
    else:
        warnings.warn("I have to auto-detect file encoding.  This may fail.  "
                      "Please specify file encoding explicitly.")
        # Test for UTF-8
        try:
            lines = codecs.open(filename, encoding="utf-8").readlines()
            encoding = "utf-8"
        except UnicodeDecodeError:
            lines = []
            # Test for Latin-1
            for line in open(filename):
                for c in line:
                    # Cheap heuristics: the characters 0x80...0x9f almost never
                    # occur in Latin-1.
                    if 0x80 <= ord(c) <= 0x9f:
                        break
                else:
                    lines.append(line.decode("latin-1"))
                    continue
                break
            else:
                encoding = "latin-1"
            if not encoding:
                # Test for cp1252
                try:
                    return codecs.open(filename, encoding="cp1252").readlines(), "cp1252", gummi_version
                except UnicodeDecodeError:
                    raise EncodingError("Couldn't auto-detect file encoding.  Please specify explicitly.",
                                        filename)
    text = process_text(u"".join(lines), filename, input_method)
    return text, encoding, gummi_version

if __name__ == "__main__":
    import doctest
    doctest.testfile("../misc/preprocessor.txt")
