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

"""Module for things that are used by (almost) all parts of Gummi.  This is
most notably the Exception classes and the global settings.

:var modulepath: path to the directory where gummi.py resides
:var preferred_encoding: the default shell encoding on the current machine

:var settings: global settings of the current Gummi process.  It is of the form
  ``settings["section.option"] = "value"``.  Everything is case-sensitive.

:type modulepath: str
:type preferred_encoding: str
:type settings: SettingsDict
"""

import re, sys, os.path, locale
import safefilename

modulepath = os.path.abspath(os.path.dirname(sys.argv[0]))
if 'epydoc' in sys.modules:
    modulepath = os.path.abspath("src/")

class Error(Exception):
    """Standard error class.
    """
    def __init__(self, description):
        """
        :Parameters:
          - `description`: error message

        :type description: string
        """
        if isinstance(description, unicode):
            # FixMe: The following must be made OS-dependent
            description = description.encode("utf-8")
        self.description = description
        Exception.__init__(self, description)

class LocalVariablesError(Error):
    """Error class for malformed lines with the local variables.
    """
    def __init__(self, description):
        """
        :Parameters:
          - `description`: error message

        :type description: string
        """
        Error.__init__(self, description)

class FileError(Error):
    """Error class for errors in a Gummi file.
    """
    def __init__(self, description, filename):
        """
        :Parameters:
          - `description`: error message
          - `filename`: Gummi file name

        :type description: string
        :type filename: string
        """
        Error.__init__(self, filename  + ": " + description)

class EncodingError(FileError):
    """Error class for encoding errors in a Gummi file.
    """
    def __init__(self, description, filename):
        """
        :Parameters:
          - `description`: error message
          - `filename`: Gummi file name

        :type description: string
        :type filename: string
        """
        FileError.__init__(self, description, filename)

def parse_local_variables(first_line, force=False, comment_marker=r"\.\. "):
    r"""Treats first_line as a line with local variables and extracts the
    key--value pairs from it.  Note that both first_line and the resulting
    dictionary contain plain strings and no unicode strings because the local
    variables are read at a time when the file encoding is still unclear.
    That's also the reason why only ASCII characters are allowed here.

        >>> parse_local_variables(".. -*- coding: utf-8; Blah: Blubb -*-\n")
        {'blah': 'blubb', 'coding': 'utf-8'}
        >>> parse_local_variables("This is not a local variables line")
        {}
        >>> parse_local_variables("; -*- coding: utf-8 -*-\n")
        {}
        >>> parse_local_variables("; -*- coding: utf-8 -*-\n", comment_marker="(#|;)")
        {'coding': 'utf-8'}

    :Parameters:
      - `first_line`: line to be parsed as a local variables line
      - `force`: if True, first_line must be a local variables line.
        Otherweise, it may also be something completely different.  This is
        important for exceptions being raised.
      - `comment_marker`: regular expression for the symbol or symbol sequence
        which marks comment lines.  Since the local variables are stored
        technically in a comment line, this routine must know it.

    :type first_line: string
    :type force: bool
    :type comment_marker: str

    :Return:
      A dictionary with the key--value pairs.  Both are strings.  If the value
      was a comma-separated list, it is a list of strings instead of a string.
      An empty dictionary if the line doesn't look like a local variables line
      at all.

    :rtype: dict

    :Exceptions:
      - `LocalVariablesError`: if the line looks like a local variables line
        but has not a valid local variables line format
    """
    local_variables_match = re.match(comment_marker+r"\s*-\*-\s*(?P<variables>.+)\s*-\*-\Z", first_line.rstrip().lower())
    if not local_variables_match:
        if force:
            raise LocalVariablesError(u"Malformed local variables line")
        else:
            return {}
    items = local_variables_match.group("variables").split(";")
    valid_pattern = re.compile(r"[a-z0-9_-]+\Z")
    local_variables = {}
    for item in items:
        if item.strip() == "":
            continue
        try:
            key, value = item.split(":")
        except:
            raise LocalVariablesError(u"Malformed local variables line")
        key, value = key.strip(), value.strip()
        if not valid_pattern.match(key):
            raise LocalVariablesError(u"Malformed key '%s' in local variables line"
                                      % key.decode("latin-1"))
        if "," in value:
            value = value.split(",")
            for v in value:
                if not valid_pattern.match(v):
                    raise LocalVariablesError(u"Malformed value '%s' local variables line"
                                              % v.decode("latin-1"))
        elif not valid_pattern.match(value):
            raise LocalVariablesError(u"Malformed value '%s' local variables line"
                                      % value.decode("latin-1"))
        local_variables[key] = value
    return local_variables


import ConfigParser, warnings, StringIO

class SettingWarning(UserWarning):
    """Warning class for invalid or unknown programm settings.  See `SettingsDict`.
    """
    pass

class SettingError(Error):
    """Error class for inconsistent settings use within Gummi.  Most errors with
    settings are mere warnings (in particular, malformed configuration files),
    however, other things must be considered internal errors.

    As a general rule of thumb, the user's mistakes are warnings, whereas
    mistakes in the source are errors.
    """
    def __init__(self, description, key, value):
        """
        :Parameters:
          - `description`: error message
          - `key`: key of the setting
          - `value`: value of the setting

        :type description: string
        :type key: string
        :type value: str, unicode, float, int, or bool
        """
        Error.__init__(self, "setting '%s = %s': %s" % (key, value, description))

import logging

class Setting(object):
    """One single Setting, this means, a key--value pair.  It is used in
    `SettingsDict` for the values in this dictionary.

    Apart from the constructor, only `set_value` should be used.  All other
    methods are for internal use only.  For examples for using this class, see
    `__init__` and `set_value`.

    :ivar key: the key of this Setting.  This may be an arbitrary non-empty
      string.  It may be divided by a dot into a section and an option part,
      where the option doesn't contain a dot, and both parts must not be
      empty.
    :ivar value: the value of this Setting.  Must be of the type described in
      `self.type`.  It may also be a list with values of that type.  It may
      also be ``None``.
    :ivar type: the type of this Setting.  It must be either ``"float"``,
      ``"int"``, ``"unicode"``, or ``"bool"``.

    :type key: unicode
    :type value: unicode, float, int, bool, list, NoneType
    :type type: str

    """
    def get_boolean(self, value):
        """Try to convert a string to a boolean.  Examples:

            >>> setting = Setting("key", "value")
            >>> setting.get_boolean("on")
            True
            >>> setting.get_boolean("off")
            False
            >>> setting.get_boolean(True)
            True
            >>> setting.get_boolean("true")
            True
            >>> setting.get_boolean("True")
            Traceback (most recent call last):
                ...
            ValueError: 'True' for setting 'key' cannot be converted to bool
            >>> setting.get_boolean(1)
            Traceback (most recent call last):
                ...
            ValueError: '1' for setting 'key' cannot be converted to bool

        :Parameters:
          - `value`: the value to be converted

        :type value: str, unicode, or bool
        
        :Return:
          The boolean value of ``value``.  If ``value`` is bool, then just
          return it.  Otherwise, compare the string with "on", "off", "true",
          "false", "yes", and "no" and return the boolean counterpart.  This
          comparison is case-sensitive.

        :rtype: bool

        :Exceptions:
          - `ValueError`: if the string could not be converted, or if it was
            neither a string nor a bool.
        """
        boolean_literals = {'yes': True, 'true': True, 'on': True,
                            'no': False, 'false': False, 'off': False}
        if isinstance(value, bool):
            return value
        if value not in boolean_literals:
            raise ValueError("'%s' for setting '%s' cannot be converted to bool" %
                             (value, self.key))
        return boolean_literals[value]
    def detect_type(self, value, source):
        """Auto-detect the type of `value` as one of the allowed types
        ``bool``, ``unicode``, ``int``, and ``float``.  `value` may also be a
        non-empty list of values; in this case the very first element is used
        for the auto-detection.  It is not checked whether the rest is of the
        same type (this is done by `adjust_value_to_type` anyway).

        For values that are taken from user-provided environment (which means
        that `source` is ``"user"``), two special syntaxes are accepted:
        parentheses and commatas make lists, so ``(1, 2, 3)`` is a list of
        three integers.  And secondly, double quotes make strings, so ``"1"``
        is a string and not an integer.  You may user the latter in the first.

        :Parameters:
          - `value`: the value the type of which should be auto-detected
          - `source`: the source of the value.  It may be "user", "direct", or
            "default".  See `__init__` for further details.

        :type value: unicode, str, int, float, or bool
        :type source: str

        :Return:
          the type of `value`, either ``"bool"``, ``"unicode"``, ``"int"``, or
          ``"float"``.

        :rtype: str

        :Exceptions:
          - `SettingError`: if the data type cannot be detected because it is
            not one of the allowed types, or if `value` is an empty list

        Examples:
        
            >>> setting = Setting("key", "value")
            >>> setting.detect_type(u"Hello", "direct")
            'unicode'
            >>> setting.detect_type("Hello", "direct")
            'unicode'
            >>> setting.detect_type(1, "direct")
            'int'
            >>> setting.detect_type(3.14, "direct")
            'float'
            >>> setting.detect_type(True, "direct")
            'bool'

        Lists also work:
        
            >>> setting.detect_type([1, 2, 3], "direct")
            'int'

        Strings are only “unpacked” if they come from the user (configuration
        file, Gummi document):
        
            >>> setting.detect_type("3.14", "user")
            'float'
            >>> setting.detect_type('"3.14"', "user")
            'unicode'
            >>> setting.detect_type("(1, 2, 3)", "user")
            'int'
            >>> setting.detect_type('("1", "2", "3")', "user")
            'unicode'

        However, the following things fail deliberately:

            >>> setting.detect_type(None, "direct")
            Traceback (most recent call last):
              ...
            SettingError: setting 'key = None': invalid type '<type 'NoneType'>'
            >>> setting.detect_type({}, "direct")
            Traceback (most recent call last):
              ...
            SettingError: setting 'key = {}': invalid type '<type 'dict'>'
            >>> setting.detect_type("(1, 2, 3]", "user")  # wrong closing parenthesis
            'unicode'
            >>> setting.detect_type([], "direct")
            Traceback (most recent call last):
              ...
            SettingError: setting 'key = []': cannot detect type of empty list
        """
        assert source in ["user", "direct", "default"]
        if isinstance(value, list):
            if len(value) == 0:
                raise SettingError("cannot detect type of empty list", self.key, value)
            single_value = value[0]
        else:
            single_value = value
        if isinstance(single_value, bool):
            return "bool"
        elif isinstance(single_value, int):
            return "int"
        elif isinstance(single_value, float):
            return "float"
        elif isinstance(single_value, basestring):
            if source == "user":
                # Test for special syntaxes: (…, …, …) and "…"
                value = value.strip()
                if value.startswith("(") and value.endswith(")"):
                    single_value = value[1:-1].split(",")[0].strip()
                else:
                    single_value = value
                if single_value.startswith('"') and single_value.endswith('"'):
                    return "unicode"
                else:
                    try:
                        int(single_value)
                    except ValueError:
                        try:
                            float(single_value)
                        except ValueError:
                            try:
                                self.get_boolean(single_value)
                            except ValueError:
                                return "unicode"
                            else:
                                return "bool"
                        else:
                            return "float"
                    else:
                        return "int"
            else:
                return "unicode"
        else:
            raise SettingError("invalid type '%s'" % type(single_value), self.key, single_value)
        assert False, "This code position should never be reached"
    def adjust_value_to_type(self, source):
        """Converts the current value of the setting to the type of this
        setting.  This type was either explicitly give or auto-detected.  In
        any case, it was determined during the construction of the Setting
        object.

        Note that this method does not check whether the current value of
        `self.value` is of the type described in `self.type`.  It just converts
        it to this type with ordinary Python means.  For example, if
        `self.value` is ``"4"`` and `self.type` is ``"int"``, then `self.value`
        is changed to ``4``.  Thus, it makes the instance consistent with
        itself.  The caller, however (`set_value` in this case), should check
        whether both types are really compatible, and not just convertible.

        :Parameters:
          - `source`: the source of the value.  It may be "user", "direct", or
            "default".  See `__init__` for further details.

        :type source: str

        :Exceptions:
          - `ValueError`: if the value cannot be converted to the type.

        Examples:

            >>> setting = Setting("key", "value")
            >>> setting.adjust_value_to_type("direct")
            >>> setting.value
            u'value'

        The following things are examples for the above mentioned implicit
        type-casting and should not happen in the actual program run, because
        `set_value` would raise an excetion before calling
        `adjust_value_to_type`.
        
            >>> setting.value = 1
            >>> setting.adjust_value_to_type("direct")
            >>> setting.value
            u'1'
            >>> setting.value = True
            >>> setting.adjust_value_to_type("direct")
            >>> setting.value
            u'True'
            >>> setting = Setting("key", 1, "float")
            >>> setting.value = "3.4"
            >>> setting.adjust_value_to_type("direct")
            >>> setting.value
            3.3999999999999999

        Examples for things that don't work:
        """
        if self.value is None:
            # In this case, typecasting is delayed until the setting gets a
            # proper value
            return
        assert self.type in ["int", "bool", "float", "unicode"]
        def convert_single_value(value, type_):
            """Converts *one* `value` to `type_`."""
            assert type_ in ["int", "bool", "float", "unicode"], "unknown type '%s'" % type_
            if type_ == "int":
                return int(value)
            elif type_ == "unicode":
                if source == "user" and value.startswith('"') and value.endswith('"'):
                    return unicode(value[1:-1])
                else:
                    return unicode(value)
            elif type_ == "bool":
                return self.get_boolean(value)
            elif type_ == "float":
                return float(value)

        if source == "user":
            assert isinstance(self.value, basestring)
            self.value = self.value.strip()
            if "," in self.value and self.value.startswith("(") and self.value.endswith(")"):
                # Okay, we have a list
                values = self.value[1:-1].split(",")
                self.value = [convert_single_value(single_value.strip(), self.type)
                              for single_value in values]
            else:
                self.value = convert_single_value(self.value, self.type)
        elif isinstance(self.value, list):
            self.value = [convert_single_value(single_value, self.type) for single_value in self.value]
        else:
            self.value = convert_single_value(self.value, self.type)
    def __init__(self, key, value, explicit_type=None, source="direct", docstring=None):
        """Create a Setting object of a given type.  After the setting object
        is initialised, there must be valid values in `self.value` and `self.type`.
        `self.type` won't be changed anymore after it.

        :Parameters:
          - `key`: the key of this setting
          - `value`: the value.  May be ``None``.
          - `explicit_type`: Optionally, you may give the type of the value
            explicitly.  It may be ``"float"``, ``"int"``, ``"bool"``, or
            ``"unicode"``.  If not given, an auto-detect is done with `value`.
            From this it follows that if `value` is ``None``, you *must* give
            an `explicit_type`.
          - `source`: the origin of this setting.  May be ``"direct"``,
            ``"user"``, or ``"default"``.  If ``"direct"``, this setting was
            created in the program code directly.  If ``"user"``, this setting
            was read from a configuration file or a key/value list in the Gummi
            source code.  If ``"default"``, the initial value is the default
            value of this setting at the same time.  Default is ``"direct"``.
          - `docstring`: a describing docstring for this setting.

        :type key: unicode
        :type value: unicode, bool, float, int, list, or ``NoneType``
        :type explicit_type: str
        :type source: str
        :type docstring: unicode or str

        :Exceptions:
          - `SettingError`: if the data type cannot be detected because it is
            not one of the allowed types, or if `value` is an empty list.  In
            particular, this is exception raised if you pass ``None`` for
            `value` and give no `explicit_type`.
          - `ValueError`: if the value cannot be converted to the
            `explicit_type`.

        Examples:

            >>> setting = Setting("key", "value")
            >>> setting.value
            u'value'
            >>> setting = Setting("key", [1, 2, 3], "unicode")
            >>> setting.value
            [u'1', u'2', u'3']

        for more examples, see `set_value`.
        """
        dot_position = key.rfind(".")
        assert 0 < dot_position < len(key) - 1 or dot_position == -1, \
            u"invalid setting key '%s', either section or option is empty" % key
        self.key, self.value, self.type, self.docstring, self.initial_source = \
            key, value, explicit_type, docstring, source
        if self.initial_source == "user":
            assert isinstance(self.value, basestring)
            self.initial_value = self.value
        self.has_default = source == "default"
        assert self.type in ["int", "float", "bool", "unicode"] or self.type is None
        if not self.type:
            self.type = self.detect_type(self.value, source)
        self.adjust_value_to_type(source)
    def set_value(self, value, source="direct", docstring=None):
        """Give the setting a new value, but of the same type as the previous
        one.
        
        :Parameters:
          - `value`: the value.  It must be of the type set in `self.type`,
            which cannot be changed after the initialisation.  It may be
            ``None``, though.
          - `source`: the source of the value.  It may be "user", "direct", or
            "default".  See `__init__` for further details.
          - `docstring`: a describing docstring for this setting.

        :type value: unicode, bool, float, int, list, or ``NoneType``
        :type source: str
        :type docstring: unicode or str

        :Exceptions:
          - `SettingError`: if the data type cannot be detected because it is
            not one of the allowed types, or if `value` is an empty list.
          - `ValueError`: if the value cannot be converted to the
            `self.type`.

        As a first example, I create a ``unicode`` setting.  Note that ``str``
        is also accepted, but internally, everything is normalised to
        ``unicode``:

            >>> setting = Setting("key", "value")
            >>> setting.set_value("Hallo")
            >>> setting.value
            u'Hallo'
            >>> setting.set_value(1)
            Traceback (most recent call last):
              ...
            SettingError: setting 'key = 1': new value of type 'int' is unequal to previous type 'unicode'

        However, as an exception to the strict typechecking, you may pass an
        ``int`` to a ``float``:

            >>> setting = Setting("key", 1.2)
            >>> setting.set_value(4)
            >>> setting.value
            4.0

        And now for user-provided values:

            >>> setting = Setting("key", 1.2)
            >>> setting.set_value("4", "user")
            >>> setting.value
            4.0
            >>> setting.set_value("(1,2,3)", "user")
            >>> setting.value
            [1.0, 2.0, 3.0]

        Default values to settings that have already a value are ignored, but
        type-checked:

            >>> setting = Setting("key", "1")
            >>> setting.set_value(1, "default")
            Traceback (most recent call last):
              ...
            SettingError: setting 'key = 1': default value of type 'int' is incompatible with previous type 'unicode'
            >>> setting.value
            u'1'
        
        Again, the exception for int/float:
        
            >>> setting = Setting("key", 4)
            >>> setting.set_value(1.2, "default")
            >>> setting.value
            4.0

        It is not unusual, for example for settings for backends, that the
        values are read from a configuration file before the defaults can be
        set.  For this case, user-provided values are typecast to ``unicode``
        when setting the default (and *only* then):

            >>> setting = Setting("key", "1", source="user")
            >>> setting.set_value("path/to/something", "default")
            >>> setting.value
            u'1'
            >>> setting = Setting("key", "(1, 2, 3)", source="user")
            >>> setting.value
            [1, 2, 3]
            >>> setting.set_value("path/to/something", "default")
            >>> setting.value
            [u'1', u'2', u'3']
        """
        if docstring:
            self.docstring = docstring
        if value is not None:
            new_type = self.detect_type(value, source)
            if new_type != self.type \
                    and not (source == "user" and self.type == "unicode") \
                    and not (source == "default" and self.initial_source == "user"
                             and new_type == "unicode") \
                    and not (source == "default" and self.type == "int" and new_type == "float") \
                    and not (source != "default" and self.type == "float" and new_type == "int"):
                if source == "default":
                    raise SettingError("default value of type '%s' is incompatible "
                                       "with previous type '%s'" %
                                       (new_type, self.type), self.key, value)
                else:
                    raise SettingError("new value of type '%s' is unequal to previous type '%s'" %
                                       (new_type, self.type), self.key, value)
        if source == "default":
            assert not self.has_default, "setting '%s' has already a default value" % self.key
            self.has_default = True
            if self.type == "int" and new_type == "float":
                self.type = new_type
            elif self.initial_source == "user" and new_type == "unicode":
                self.type = new_type
        else:
            self.value = value
        self.adjust_value_to_type(source)

class SettingsDict(dict):
    """Class for program settings, especially the global ones.  They may come
    from an INI file, or from the command line, or whereever.  Their keys (the
    keys in this dict) may be of the form “section.option”.  If read from a
    configuration file, this form is mandatory.  Everything is case-sensitive
    here, as usual in Gummi.

    As an example, consider the following configuration file:

        >>> print open("../misc/test.conf").read()
        # -*- coding: utf-8 -*-
        # Paths are given in a form suitable for the respective operating system.  This
        # includes the pathname component separator ("/" on POSIX, "/" or "\\" on
        # Windows) as well as the path separator (":" on POSIX, ";" on Windows).
        #
        # This means that default configurations files shipped with the Gummi
        # distribution must be adjusted for the respective platform.
        [Paths]
        backends = %(rootdir)s/src/backends
        [General]
        quiet = true
        [Veröffentlichung]
        supi = toll
        <BLANKLINE>

    Then, SettingsDict works like this:

        >>> os.environ["HOME"] = "/home/user"
        >>> settings = SettingsDict()
        >>> settings.set_default("General.quiet", True)
        >>> settings.set_predefined_variable("rootdir", "~/src/bobcat/")
        >>> settings.load_from_files("../misc/test.conf")
        ['../misc/test.conf']
        >>> for key in settings:
        ...     key, settings[key]
        ...
        (u'Ver\\xf6ffentlichung.supi', u'toll')
        (u'Paths.backends', u'/home/user/src/bobcat/src/backends')
        ('General.quiet', True)

    As you can see, all settings set in the section “Paths” are expanded to
    absolute pathnames, with »~« working.
    """
    def __init__(self):
        self.predefined_variables = {}
        self.closed_sections = set()
        self.logger = logging.getLogger("gummi.settings")
    def set_predefined_variable(self, name, value):
        """Set a predefined variable for use in configuration files.  See the
        general explanation in `SettingsDict` for an example.  There, the
        predefined variable is called ``rootdir``.

        :Parameters:
          - `name`: name of the predefined variable
          - `value`: value of the variable, this is substituted wherever the
            variable is used in the configuration file

        :type name: unicode
        :type value: unicode
        """
        assert name not in self.predefined_variables, \
            u"predefined variable '%s' is already set to value '%s'" % \
            (name, self.predefined_variables[name])
        self.predefined_variables[name] = value
    def test_for_closed_section(self, key, value):
        """Check whether the given key belongs to a section that is already
        *closed*, which means that no new keys are accepted in that section.
        If this is the case, an `SettingError` exception is raised.  Sections
        are closed with `close_section`.

        The rationale behind this is that it helps to detect typos in
        configuration files: First, all defaults for a certain section are
        defined in the program, then it is closed, and then the configuration
        file is read.  Thus, only known keys may appear in the file, whilest
        all others trigger a warning.

        Note that this also works if the defaults are defined *after* reading
        the configuration files (and closing the sections even after this).
        This is important especially for backends, which are imported in a
        later phase.

        Also note that the exception is raised if the key belongs to a closed
        section, and *not* only if it is a *new* key in a closed section.

        :Parameters:
          - `key`: the key to be checked
          - `value`: the value of that key; this is used here only to generate
            a proper error message if necessary

        :type key: unicode
        :type value: unicode, int, float, bool, list

        :Exceptions:
          - `SettingError`: if the key belongs to a closed section

        Example:
        
            >>> settings = SettingsDict()
            >>> settings.set_default("General.quiet", True)
            >>> settings.close_section("General")
            >>> settings.set_predefined_variable("rootdir", "~/src/bobcat/")
            >>> settings.load_from_files("../misc/test.conf")
            ['../misc/test.conf']
            >>> settings.test_for_closed_section("Unknown.section.quiet", False)
            >>> settings.test_for_closed_section("General.quiet", False)
            Traceback (most recent call last):
              ...
            SettingError: setting 'General.quiet = False': unknown setting key; section already closed
            >>> settings.test_for_closed_section("General.quite", False)
            Traceback (most recent call last):
              ...
            SettingError: setting 'General.quite = False': unknown setting key; section already closed

        """
        dot_position = key.rfind(".")
        assert 0 < dot_position < len(key) - 1 or dot_position == -1, \
            u"invalid setting '%s', either section or option is empty" % key
        if dot_position != -1:
            section = key[:dot_position]
            if section in self.closed_sections:
                raise SettingError(u"unknown setting key; section already closed", key, value)
    def set_default(self, key, value, explicit_type=None, docstring=None):
        """Set the default value of a setting.  It may already exist or not.

        :Parameters:
          - `key`: the full section.option key
          - `value`: the default value.
          - `explicit_type`: type of ``value``.  May be ``"unicode"``, ``"str"``,
            ``"int"``, ``"float"``, or ``"bool"``.  If not given, an
            auto-detect is tried to detect the type.  In particular, if
            ``value`` is "yes", "no", "true" etc., then "bool" is assumed.
          - `docstring`: a docstring describing this setting

        :type key: unicode
        :type value: unicode, str, float, int, bool, or ``None``
        :type explicit_type: str
        :type docstring: unicode

        Examples:

            >>> warnings.simplefilter("error")  # Turn warnings into errors, just for testing
            >>> settings = SettingsDict()
            >>> settings.set_default("General.a", "Hallo")
            >>> settings.set_default("General.b", "on")
            >>> settings.set_default("General.c", 1)
            >>> settings.set_default("General.d", 4.5)
            >>> settings.set_default("General.e", None, "unicode")
            >>> settings
            {'General.c': 1, 'General.b': u'on', 'General.a': u'Hallo', 'General.e': None, 'General.d': 4.5}

        Now, we can index it (see `__setitem__`).

            >>> settings["General.b"] = True
            Traceback (most recent call last):
              ...
            SettingError: setting 'General.b = True': new value of type 'bool' is unequal to previous type 'unicode'
            >>> settings["General.quiet"] = True
            >>> settings.close_section("General")
            Traceback (most recent call last):
                ...
            SettingWarning: unknown setting 'General.quiet' ignored
            >>> settings["General.f"] = "offf"
            Traceback (most recent call last):
                ...
            SettingError: setting 'General.f = offf': unknown setting key; section already closed
            >>> settings["General."] = "offf"
            Traceback (most recent call last):
                ...
            AssertionError: invalid setting 'General.', either section or option is empty
            >>> settings.set_default("General.f", [1,2,3,4])
            Traceback (most recent call last):
                ...
            SettingError: setting 'General.f = [1, 2, 3, 4]': unknown setting key; section already closed
        """
        assert key not in self or not super(SettingsDict, self).__getitem__(key).has_default, \
            u"setting '%s' has already a default value (%s)" % (key, repr(self[key]))
        self.test_for_closed_section(key, value)
        if key in self:
            super(SettingsDict, self).__getitem__(key).set_value(value, "default", docstring)
        else:
            super(SettingsDict, self).__setitem__(key, Setting(key, value, explicit_type,
                                                               "default", docstring))
    def __setitem__(self, key, value):
        """Assign ``value`` to the setting ``key``.

        :Parameters:
          - `key`: the full section.option key
          - `value`: the new contents of this setting

        :type key: unicode
        :type value: unicode, str, float, int, bool, or NoneType
        """
        if key in self:
            super(SettingsDict, self).__getitem__(key).set_value(value)
        else:
            self.test_for_closed_section(key, value)
            super(SettingsDict, self).__setitem__(key, Setting(key, value))
    def __getitem__(self, key):
        """Return the value of a given setting.  The setting is given by its
        key.

        :Parameters:
          - `key`: the full section.option key

        :type key: unicode

        :Return:
          the value of the key

        :rtype: unicode, bool, int, float, NoneType, list
        """
        return super(SettingsDict, self).__getitem__(key).value
    def close_section(self, section):
        """Forbid any further new keys in a section.  By closing a section, you
        forbid so-far unknown keys in a section, and you can't set further
        default values in this section.  See `test_for_closed_section` for more
        information and an example.

        :Parameters:
          - `section`: the name of the section that is to be closed

        :type section: unicode
        """
        self.closed_sections.add(section)
        len_section = len(section)
        keys_in_section = [key for key in self.keys()
                           if key.startswith(section+".")
                           and len(key) > len_section + 1
                           and not "." in key[len_section+1:]]
        for key in keys_in_section:
            if not super(SettingsDict, self).__getitem__(key).has_default:
                del self[key]
                warnings.warn(SettingWarning(u"unknown setting '%s' ignored" % key),
                              stacklevel=2)
                assert key not in self
    def parse_keyvalue_list(self, excerpt):
        pass
    def load_from_files(self, filenames, forbidden_sections=frozenset()):
        """Reads Windows-like INI files.  Inspired by
        <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65334>.  The
        very first line of the config files may be a comment line with
        Emacs-like encoding information.  If this is not present, the default
        encoding is UTF-8.

        All values in the section ``[Path]`` are converted and normalized to
        absolute pathnames according to the current directory.  Values in all
        other sections are converted to arbitrary types using
        `Setting.detect_type` and `Setting.adjust_value_to_type`.

        For examples, see the general explanations for `SettingsDict` and
        `test_for_closed_section`.

        :Parameters:
          - `filenames`: list of filenames of INI files.  They are processed in the
            given order.  It may also be a single filename.
          - `forbidden_sections`: sequence type (list, set etc) with the names
            of sections that must not occur in the configuration files.  If
            they do, they are ignored with a warning.

        :type filenames: list or str
        :type forbidden_sections: set

        :Return:
          names of all files that were actually read

        :rtype: list of str
        """
        if isinstance(filenames, basestring):
            filenames = [filenames]
        read_files = []
        for filename in filenames:
            try:
                payload = open(filename).read()
            except IOError:
                continue
            try:
                encoding = parse_local_variables(payload.splitlines()[0],
                                                 comment_marker="(#|;)").get("coding", "utf-8")
            except IndexError:
                encoding = "utf-8"
            try:
                payload_file = StringIO.StringIO(payload.decode(encoding))
            except UnicodeDecodeError:
                warnings.warn(SettingWarning(u"invalid encoding in file %s; "
                                             u"skipped this file" % filename), stacklevel=2)
                continue
            config_parser = ConfigParser.SafeConfigParser()
            config_parser.optionxform = lambda s: s    # Make options case-sensitive
            config_parser.readfp(payload_file, filename)
            for section in config_parser.sections():
                if section in forbidden_sections:
                        warnings.warn(SettingWarning(u"section '%s' is forbidden in config "
                                                     u"file; it was ignored" % section))
                        continue
                for option in config_parser.options(section):
                    key = section + "." + option
                    if "." in option:
                        warnings.warn(SettingWarning(u"setting '%s' contains a dot in the "
                                                     u"option part; it was ignored" % key))
                        continue
                    try:
                        value = config_parser.get(section, option, vars=self.predefined_variables).strip()
                        if section == "Paths":
                            value = os.path.abspath(os.path.expanduser(value))
                        if key in self:
                            super(SettingsDict, self).__getitem__(key).set_value(value, "user")
                        else:
                            self.test_for_closed_section(key, value)
                            super(SettingsDict, self).__setitem__(key, Setting(key, value, source="user"))
                    except ConfigParser.InterpolationMissingOptionError, e:
                        warnings.warn(SettingWarning(u"setting '%s' misses predefined variable '%s'" %
                                                    (key, e.reference)))
                    except SettingError, e:
                        warnings.warn(SettingWarning(u'file "%s": ' % filename + e.description),
                                      stacklevel=2)
            read_files.append(filename)
        return read_files
    def __repr__(self):
        result = "{"
        for i, key in enumerate(self):
            result += "%r: %r" % (key, self[key])
            if i < len(self) - 1:
                result += ", "
        return result + "}"
        
settings = SettingsDict()

settings.set_default("input filename", "", docstring="""
    The absolute path to the Gummi input filename.  Must be `None` if the input
    doesn't come from a file.""")
settings.set_default("output path", None, "unicode", docstring="""
    The destination path or filename.  For the PDF backend, it will be a file,
    for the HTML backend, it may be a single file or a directory.  Note that
    this is the settings that was given by the user, so it may also be ``None``.
    ``None`` means that the backend has to calculate the proper output path
    itself (from the input filename, for example).""")
settings.set_default("backend", None, "unicode", docstring="""
    The "official" name of the backend in all-lowercase, e.g. "latex" or
    "html".""")


import logging
def setup_logging(logfile_name=None, do_logging=True, level=logging.DEBUG):
    """Start the logging facility if the caller whishes this.  Every module in
    Gummi can then write to the logfile by saying::

        import logging
        logger = logging.getLogger("gummi.module.submodule")
        logger.error("Something went wrong")

    By the way, ``getLogger`` returns a singleton object, so everything really
    goes into the same logfile.

    :Parameters:
      - `logfile_name`: file name of the logfile.  Don't do logging if this is
        ``None``.
      - `do_logging`: do logging only if this is ``True``
      - `level`: logging level, see
        http://docs.python.org/lib/module-logging.html

    :type logfile_name: str
    :type do_logging: bool
    :type level: int
    """
    if do_logging and logfile_name:
        logging.basicConfig(level=level, filename=logfile_name, filemode="w",
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            format="%(asctime)s %(name)s %(levelname)-8s %(message)s")
    else:
        class LogSink(object):
            def write(self, *args, **kwargs): pass
            def flush(self, *args, **kwargs): pass
        logging.basicConfig(stream=LogSink())



if __name__ == "__main__":
    import doctest
    doctest.testmod()
    doctest.testfile("../misc/common.txt")
