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

"""Handling of global and local settings dictionaries.  This includes
configuration files as well es key/value pairs that are parsed in the Bobcat
document.

:var settings: global settings of the current Bobcat process.  It is of the form
  ``settings["section.option"] = "value"``.  Everything is case-sensitive.

:type settings: SettingsDict
"""

import ConfigParser, warnings, StringIO, logging, os, re
from . import common

class SettingWarning(UserWarning):
    """Warning class for invalid or unknown programm settings.  See `SettingsDict`.
    """
    pass

class SettingError(common.Error):
    """Error class for inconsistent settings use within Bobcat.  Most errors with
    settings are mere warnings (in particular, malformed configuration files),
    however, other things must be considered internal errors.

    As a general rule of thumb, the user's mistakes are warnings, whereas
    mistakes in the source are errors.

    :ivar key: the key of the error provoking key/value pair
    :ivar value: the key of the error provoking key/value pair

    :type key: unicode
    :type value: unicode, float, int, bool or NoneType
    """
    def __init__(self, description, key, value):
        """
        :Parameters:
          - `description`: error message
          - `key`: key of the setting
          - `value`: value of the setting

        :type description: unicode
        :type key: unicode
        :type value: str, unicode, float, int, or bool
        """
        super(SettingError, self).__init__("setting '%s = %s': %s" % (key, value, description))
        self.key, self.value = key, value

class SettingUnknownKeyError(SettingError):
    """Error class for invalid keys.  A key is invalid if the section it
    belongs to has been closed already, and it was not previously defined in
    this section.
    """
    def __init__(self, key, value):
        """
        :Parameters:
          - `key`: key of the setting
          - `value`: value of the setting

        :type key: unicode
        :type value: str, unicode, float, int, or bool
        """
        super(SettingUnknownKeyError, self).__init__(
            u"unknown setting key; section already closed", key, value)

class SettingInvalidKeyValueListError(SettingError):
    """Error class for invalid syntaxes in key/value lists.  Note that this is
    raised only in case of a bad list syntax, not if there was a problem with
    adding a parsed key/value pair to the `SettingsDict`.
    """
    def __init__(self, excerpt):
        """
        :Parameters:
          - `excerpt`: the part of the list that couldn't be parsed

        :type excerpt: `preprocessor.Excerpt`
        """
        super(SettingInvalidKeyValueListError, self).__init__(
            u"unparsable key found in key/value list", key=excerpt, value=None)

class SettingWrongTypeError(SettingError):
    """Error class for invalid types of values in a `SettingsDict`.  A type is
    invalid if there is already a value stored for the respective key in the
    dictionary, but this type is incompative with the one that is to be stored
    with the new value.

    :ivar previous_type: the hitherto type of the value
    :ivar new_type: the type that was tried to set now; it should have been
      equal to `previous_type`, yet it wasn't.

    :type previous_type: str
    :type new_type: str
    """
    def __init__(self, key, value, previous_type, new_type):
        """
        :Parameters:
          - `key`: key of the setting
          - `value`: value of the setting
          - `previous_type`: the hitherto type of the value
          - `new_type`: the type that was tried to set now

        :type key: unicode
        :type value: str, unicode, float, int, or bool
        :type previous_type: str
        :type new_type: str
        """
        super(SettingWrongTypeError, self).__init__(
            "new value of type '%s' is unequal to previous type '%s'" % (new_type, previous_type),
            key, value)
        self.previous_type, self.new_type = previous_type, new_type

class SettingInvalidSectionError(SettingError):
    """Error class for invalid section names.  This error is raised if you try
    to add a new key to a `SettingsDict` that belongs to a section that hasn't
    occured yet in this dictionary (i.e. there is no key in this
    ``SettingsDict`` of the same section), *and* this dictionary inhibits new
    sections.  This means, `SettingsDict.inhibit_new_sections` has been called.
    
    :ivar section: the section name that provoked this error

    :type section: unicode
    """
    def __init__(self, key, value, section):
        """
        :Parameters:
          - `key`: key of the setting
          - `value`: value of the setting
          - `section`: the section name that provoked this error

        :type key: unicode
        :type value: str, unicode, float, int, or bool
        :type section: unicode
        """
        super(SettingInvalidSectionError, self).__init__(u"invalid section used in key", key, value)
        self.section = section

class Setting(object):
    """One single Setting, this means, a key--value pair.  It is used in
    `SettingsDict` for the values in this dictionary.

    Apart from the constructor, only `set_value` should be used.  All other
    methods are for internal use only.  For examples for using this class, see
    `__init__` and `set_value`.

    :ivar key: The key of this Setting.  It is stored in this class only for
      gernerating proper error messages.  This may be an arbitrary non-empty
      string.  It may be divided by a dot into a section and an option part,
      where the option doesn't contain a dot, and both parts must not be empty.
      If there is no dot, the section is ``u""``.
    :ivar value: the value of this Setting.  Must be of the type described in
      `self.type`.  It may also be a list with values of that type.  It may
      also be ``None``.
    :ivar type: the type of this Setting.  It must be either ``"float"``,
      ``"int"``, ``"unicode"``, or ``"bool"``.
    :ivar __initial_source: the source that was given when the setting was
      created
    :ivar __preliminarily_detected_value: The value that was given when the setting was
      created.  It extists only if the source during initialisation was ``"conf
      file"`` or ``"keyval list"``.

    :type key: unicode
    :type value: unicode, float, int, bool, list, NoneType
    :type type: str
    :type __initial_source: str
    :type __preliminarily_detected_value: unicode

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

        For values that are taken from a configuration file (which means that
        `source` is ``"conf file"``), two special syntaxes are accepted:
        parentheses and commatas make lists, so ``(1, 2, 3)`` is a list of
        three integers.  And secondly, double quotes make strings, so ``"1"``
        is a string and not an integer.  You may user the latter in the first.

        :Parameters:
          - `value`: the value the type of which should be auto-detected
          - `source`: the source of the value.  It may be "conf file", "keyval
            list", "direct", or "default".  See `__init__` for further
            details.

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

        Lists also work, here the first element is used for the detection:
        
            >>> setting.detect_type([1, 2, 3], "direct")
            'int'

        Strings are only “unpacked” if they come from the user (configuration
        file, Bobcat document):
        
            >>> setting.detect_type("3.14", "conf file")
            'float'
            >>> setting.detect_type("3.14", "keyval list")
            'float'
            >>> setting.detect_type('"3.14"', "conf file")
            'unicode'
            >>> setting.detect_type("(1, 2, 3)", "conf file")
            'int'
            >>> setting.detect_type('("1", "2", "3")', "conf file")
            'unicode'

        Note that for a key/value list, the special syntaxes with ``"…"`` and
        ``(…, …, …)`` are not supported:

            >>> setting.detect_type("(1, 2, 3)", "keyval list")
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
            >>> setting.detect_type("(1, 2, 3]", "conf file")  # wrong parenthesis
            'unicode'
            >>> setting.detect_type([], "direct")
            Traceback (most recent call last):
              ...
            SettingError: setting 'key = []': cannot detect type of empty list

        """
        # pylint: disable-msg=R0912
        assert source in ["conf file", "keyval list", "direct", "default"]
        if isinstance(value, list):
            if len(value) == 0:
                raise SettingError("cannot detect type of empty list", self.key, value)
            single_value = value[0]
        else:
            single_value = value
        detected_type = None
        if isinstance(single_value, bool):
            detected_type = "bool"
        elif isinstance(single_value, int):
            detected_type = "int"
        elif isinstance(single_value, float):
            detected_type = "float"
        elif isinstance(single_value, basestring):
            if source not in ["conf file", "keyval list"]:
                detected_type = "unicode"
            else:
                # Test for special syntaxes: (…, …, …) and "…"
                value = value.strip()
                if source == "conf file" and value.startswith("(") and value.endswith(")"):
                    single_value = value[1:-1].split(",")[0].strip()
                else:
                    single_value = value
                if source == "conf file" and \
                        single_value.startswith('"') and single_value.endswith('"'):
                    detected_type = "unicode"
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
                                detected_type = "unicode"
                            else:
                                detected_type = "bool"
                        else:
                            detected_type = "float"
                    else:
                        detected_type = "int"
        else:
            raise SettingError("invalid type '%s'" % type(single_value), self.key, single_value)
        assert detected_type in ["unicode", "bool", "int", "float"]
        return detected_type
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
          - `source`: the source of the value.  It may be "conf file", "keyval
            list", "direct", or "default".  See `__init__` for further details.

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

        """
        # pylint: disable-msg=R0912
        assert source in ["direct", "default", "conf file", "keyval list"]
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
                if source == "conf file" and value.startswith('"') and value.endswith('"'):
                    return unicode(value[1:-1])
                else:
                    return unicode(value)
            elif type_ == "bool":
                return self.get_boolean(value)
            elif type_ == "float":
                return float(value)

        if source in ["conf file", "keyval list"]:
            assert isinstance(self.value, basestring)
        if source == "conf file":
            self.value = self.value.strip()
            if "," in self.value and self.value.startswith("(") and self.value.endswith(")"):
                # Okay, we have a list
                values = self.value[1:-1].split(",")
                self.value = [convert_single_value(single_value.strip(), self.type)
                              for single_value in values]
            else:
                self.value = convert_single_value(self.value, self.type)
        elif isinstance(self.value, list):
            self.value = [convert_single_value(single_value, self.type)
                          for single_value in self.value]
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
          - `source`: the origin of this setting.  May be ``"direct"``, ``"conf
            file"``, ``"keyval list"``, or ``"default"``.  If ``"direct"``,
            this setting was created in the program code directly.  If ``"conf
            file"``, this setting was read from a configuration file.  If
            ``"keyval list"``, this settings comes from a key/value list in a
            Bobcat source file (see `SettingsDict.parse_keyvalue_list`).  If
            ``"default"``, the initial value is the default value of this
            setting at the same time.  Default is ``"direct"``.
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
        # FixMe: Maybe one should drop the ``explicit_type`` argument because
        # it forces `adjust_value_to_type` to support spurious cases, see the
        # unit test file for this module for more information.
        dot_position = key.rfind(".")
        assert 0 < dot_position < len(key) - 1 or dot_position == -1, \
            u"invalid setting key '%s', either section or option is empty" % key
        self.key, self.value, self.type, self.docstring, self.__initial_source = \
            key, value, explicit_type, docstring, source
        if self.__initial_source in ["conf file", "keyval list"]:
            assert isinstance(self.value, basestring)
            self.__preliminarily_detected_value = self.value
        else:
            self.__preliminarily_detected_value = None
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
          - `source`: the source of the value.  It may be "conf file", "keyval
            list", "direct", or "default".  See `__init__` for further details.
          - `docstring`: a describing docstring for this setting.

        :type value: unicode, bool, float, int, list, or ``NoneType``
        :type source: str
        :type docstring: unicode or str

        :Exceptions:
          - `SettingError`: if the data type cannot be detected because it is
            not one of the allowed types, or if `value` is an empty list.
          - `SettingWrongTypeError`: if the new value is incompatible with the
            already stored one, including the case if the new value is the
            default value
          - `ValueError`: if the value cannot be converted to the
            `self.type`.

        As a first example, I create a ``unicode`` setting.  Note that ``str``
        is also accepted, but internally, everything is normalised to
        ``unicode``:

            >>> setting = Setting("key", "value")
            >>> setting.set_value("Hallo")
            >>> setting.value
            u'Hallo'
            >>> setting.set_value(1)  #doctest:+NORMALIZE_WHITESPACE
            Traceback (most recent call last):
              ...
            SettingWrongTypeError: setting 'key = 1': new value of type 'int' is
            unequal to previous type 'unicode'

        However, as an exception to the strict typechecking, you may pass an
        ``int`` to a ``float``:

            >>> setting = Setting("key", 1.2)
            >>> setting.set_value(4)
            >>> setting.value
            4.0

        And now for user-provided values:

            >>> setting = Setting("key", 1.2)
            >>> setting.set_value("4", "conf file")
            >>> setting.value
            4.0
            >>> setting.set_value("(1,2,3)", "conf file")
            >>> setting.value
            [1.0, 2.0, 3.0]

        Default values to settings that have already a value are ignored, but
        type-checked:

            >>> setting = Setting("key", "1")
            >>> setting.set_value(1, "default")  #doctest:+NORMALIZE_WHITESPACE
            Traceback (most recent call last):
              ...
            SettingWrongTypeError: setting 'key = 1': new value of type 'int'
            is unequal to previous type 'unicode'
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

            >>> setting = Setting("key", "1", source="conf file")
            >>> setting.set_value("path/to/something", "default")
            >>> setting.value
            u'1'
            >>> setting = Setting("key", "(1, 2, 3)", source="conf file")
            >>> setting.value
            [1, 2, 3]
            >>> setting.set_value("path/to/something", "default")
            >>> setting.value
            [u'1', u'2', u'3']

        """
        def type_actually_unicode():
            """Returns ``True`` if the new type of the setting is supposed to
            be unicode, however, the old type way detected from the value from
            a configuration file or a key/value list so it may have been
            unicode in the first place, just improperly auto-detected.

            In this case, no error should be generated but just converted to
            the initial(!) unicode values as it was in the configuration file
            or the key/value list.
            """
            return source in ["default", "direct"] and \
                self.__preliminarily_detected_value is not None and new_type == "unicode"
        if docstring:
            self.docstring = docstring
        if value is not None:
            new_type = self.detect_type(value, source)
            if new_type != self.type \
                    and not (source in ["conf file", "keyval list"] and self.type == "unicode") \
                    and not type_actually_unicode() \
                    and not (source == "default" and self.type == "int" and new_type == "float") \
                    and not (source != "default" and self.type == "float" and new_type == "int"):
                raise SettingWrongTypeError(self.key, value, self.type, new_type)
        else:
            new_type = None
        if source == "default":
            assert not self.has_default, "setting '%s' has already a default value" % self.key
            self.has_default = True
            if self.type == "int" and new_type == "float":
                self.type = new_type
        else:
            self.value = value
        if type_actually_unicode():
            self.type = new_type  # always "unicode"
            if source == "default":
                self.value = self.__preliminarily_detected_value
                # because the new value must be completely re-parsed
                source = self.__initial_source
        if source == "direct":
            self.__preliminarily_detected_value = None
        self.adjust_value_to_type(source)

class SettingsDict(dict):
    """Class for program settings, especially the global ones.  They may come
    from an INI file, or from the command line, or whereever.  Their keys (the
    keys in this dict) may be of the form “section.option”.  If read from a
    configuration file, this form is mandatory.  If it is just of the form
    “option” (without a dot), the section is ``u""``.  Note that “.option” is
    invalid.  Everything is case-sensitive here, as usual in Bobcat.

    As an example, consider the following configuration file:

        >>> print open("test.conf").read()
        # -*- coding: utf-8 -*-
        # Paths are given in a form suitable for the respective operating system.  This
        # includes the pathname component separator ("/" on POSIX, "/" or "\\" on
        # Windows) as well as the path separator (":" on POSIX, ";" on Windows).
        #
        # This means that default configurations files shipped with the Bobcat
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
        >>> settings.load_from_files("test.conf")
        ['test.conf']
        >>> for key in settings:
        ...     key, settings[key]
        ...
        (u'Ver\\xf6ffentlichung.supi', u'toll')
        (u'Paths.backends', u'/home/user/src/bobcat/src/backends')
        (u'General.quiet', True)

    As you can see, all settings set in the section “Paths” are expanded to
    absolute pathnames, with »~« working.
    """
    def __init__(self):
        super(SettingsDict, self).__init__()
        self.predefined_variables = {}
        self.closed_sections = set()
        self.__new_sections_inhibited = False
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

        This also tests whether a completely new section would be opened by
        this key, and checks whether it is allowed to open it.  See
        `inhibit_new_sections` for further details.

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
          - `SettingUnknownKeyError`: if the key belongs to a closed section
          - `SettingInvalidSectionError`: if the section hasn't existed yet,
            and no new sections are allowed

        Example:
        
            >>> settings = SettingsDict()
            >>> settings.set_default("General.quiet", True)
            >>> settings.close_section("General")
            >>> settings.set_predefined_variable("rootdir", "~/src/bobcat/")
            >>> settings.load_from_files("test.conf")
            ['test.conf']
            >>> settings.test_for_closed_section("Unknown.section.quiet", False)
            >>> settings.test_for_closed_section("General.quiet", False)
            ...                                    #doctest:+NORMALIZE_WHITESPACE
            Traceback (most recent call last):
              ...
            SettingUnknownKeyError: setting 'General.quiet = False': unknown setting key;
            section already closed
            >>> settings.test_for_closed_section("General.quite", False)
            ...                                     #doctest:+NORMALIZE_WHITESPACE
            Traceback (most recent call last):
              ...
            SettingUnknownKeyError: setting 'General.quite = False': unknown setting key;
            section already closed

        """
        dot_position = key.rfind(".")
        assert 0 < dot_position < len(key) - 1 or dot_position == -1, \
            u"invalid setting '%s', either section or option is empty" % key
        section = key[:dot_position] if dot_position != -1 else u""
        if section in self.closed_sections:
            raise SettingUnknownKeyError(key, value)
        if self.__new_sections_inhibited and section not in self.sections:
            raise SettingInvalidSectionError(key, value, section)
    def __eq__(self, other):
        # For comparison, we have to normalise both operands first by replacing
        # the values (which are `Setting` objects) by their "effective" value
        # (the result of `Setting.value`).
        if isinstance(other, SettingsDict):
            other = dict((key, other[key]) for key in other)
        return dict((key, self[key]) for key in self) == other
    def __ne__(self, other):
        return not self.__eq__(other)
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
            >>> settings  #doctest:+NORMALIZE_WHITESPACE
            {'General.c': 1, 'General.b': u'on', 'General.a': u'Hallo', 'General.e': None,
            'General.d': 4.5}

        Now, we can index it (see `__setitem__`).

            >>> settings["General.b"] = True  #doctest:+NORMALIZE_WHITESPACE
            Traceback (most recent call last):
              ...
            SettingWrongTypeError: setting 'General.b = True': new value of type 'bool'
            is unequal to previous type 'unicode'
            >>> settings["General.quiet"] = True
            >>> settings.close_section("General")
            Traceback (most recent call last):
                ...
            SettingWarning: unknown setting 'General.quiet' ignored
            >>> settings["General.f"] = "offf"  #doctest:+NORMALIZE_WHITESPACE
            Traceback (most recent call last):
                ...
            SettingUnknownKeyError: setting 'General.f = offf': unknown setting key;
            section already closed
            >>> settings["General."] = "offf"
            Traceback (most recent call last):
                ...
            AssertionError: invalid setting 'General.', either section or option is empty
            >>> settings.set_default("General.f", [1,2,3,4])  #doctest:+NORMALIZE_WHITESPACE
            Traceback (most recent call last):
                ...
            SettingUnknownKeyError: setting 'General.f = [1, 2, 3, 4]': unknown setting
            key; section already closed

        """
        assert key not in self or not super(SettingsDict, self).__getitem__(key).has_default, \
            u"setting '%s' has already a default value (%s)" % (key, repr(self[key]))
        self.test_for_closed_section(key, value)
        if key in self:
            super(SettingsDict, self).__getitem__(key).set_value(value, "default", docstring)
        else:
            super(SettingsDict, self).__setitem__(key, Setting(key, value, explicit_type,
                                                               "default", docstring))
    def store_new_value(self, key, value, source="direct"):
        """Assign ``value`` to the setting ``key``.

        :Parameters:
          - `key`: the full section.option key
          - `value`: the new contents of this setting
          - `source`: the source of the value.  It may be "conf file",
            "direct", or "default".  See `Setting.__init__` for further
            details.

        :type key: unicode
        :type value: unicode, str, float, int, bool, or NoneType
        :type source: str
        """
        if key in self:
            old_value = super(SettingsDict, self).__getitem__(key)
            old_value.set_value(value, source)
            # I kill the old key because the new one could be an Excerpt while
            # the old was a unicode.  However, I want the Excerpt.
            super(SettingsDict, self).__delitem__(key)
            super(SettingsDict, self).__setitem__(key, old_value)
        else:
            self.test_for_closed_section(key, value)
            super(SettingsDict, self).__setitem__(key, Setting(key, value, source=source))
    def __setitem__(self, key, value):
        """Assign ``value`` to the setting ``key``.  This is mere syntactic
        sugar for the more awkward `store_new_value`.

        :Parameters:
          - `key`: the full section.option key
          - `value`: the new contents of this setting

        :type key: unicode
        :type value: unicode, str, float, int, bool, or NoneType
        """
        self.store_new_value(key, value)
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
          - `section`: the name of the section that is to be closed.  If it is
            the empty string, the section-free domain, i.e. all settings
            without a section in them (i.e., without a dot in the key), is
            closed.

        :type section: unicode
        """
        self.closed_sections.add(section)
        if section != u"":
            len_section = len(section)
            keys_in_section = [key for key in self.iterkeys()
                               if key.startswith(section+".")
                               and len(key) > len_section + 1
                               and not "." in key[len_section+1:]]
        else:
            keys_in_section = [key for key in self.iterkeys() if not "." in key]
        for key in keys_in_section:
            if not super(SettingsDict, self).__getitem__(key).has_default:
                del self[key]
                warnings.warn(SettingWarning(u"unknown setting '%s' ignored" % key),
                              stacklevel=2)
                assert key not in self
    def inhibit_new_sections(self):
        """Inhibit new keys from previously unknown sections.  When this method
        is called, from now on it is impossible to add new keys coming from
        sections that haven't yet occured in this dictionary.

        Note that the set of valid section names is generated when this method
        is called.  This means that sections of keys that used to be in this
        dictionary but have been deleted already are not considered.

            >>> settings = SettingsDict()
            >>> settings.set_default("General.quiet", True)
            >>> settings.inhibit_new_sections()
            >>> settings.set_default("General.outfile", None, "unicode")
            >>> settings.set_default("Newsection.outfile", None, "unicode")
            ...                                   #doctest:+NORMALIZE_WHITESPACE
            Traceback (most recent call last):
                ...
            SettingInvalidSectionError: setting 'Newsection.outfile = None': invalid
            section used in key

        Note that this also applies to new section-less keys.  The “section
        with empty name” must also be known in order to accept new keys:

            >>> settings["sectionlesskey"] = 0  #doctest:+NORMALIZE_WHITESPACE
            Traceback (most recent call last):
                ...
            SettingInvalidSectionError: setting 'sectionlesskey = 0': invalid
            section used in key

        """
        if not self.__new_sections_inhibited:
            self.__new_sections_inhibited = True
            self.sections = set()
            for key in self.iterkeys():
                dot_position = key.rfind(".")
                if dot_position != -1:
                    self.sections.add(unicode(key)[:dot_position])
                else:
                    self.sections.add(u"")
    def parse_keyvalue_list(self, excerpt, parent_element=None,
                            item_separator=u",", key_terminators=u":="):
        """Adds items from a key/value list to the dictionary.  These key/value
        lists are most commonly found in Bobcat source documents, in similar
        places as in LaTeX.  You can use this method to build mini settings
        dictionaries in order to parse these lists.  The keys remain Excerpts,
        so that you can reconstruct the original positons in case of errors.

        The following characters are allowed in keys: All alphanumerical
        codepoins of Unicode, Unicode whitespace (which is normalised, though),
        and any character in ``@^!$%&/?*~\#|><_``.  Moreover, the dot ``.`` is
        allowed for dividing section and option.

        If the separator between key and value as well as the value itself is
        omitted, a boolean ``True`` is assumed for the value.

        :Parameters:
          - `excerpt`: the Excerpt which contains the complete key/value list
            to be parsed
          - `parent_element`: The document element in which this key/value list
            occurs.  This is used for generating cumulative errors, if given.
          - `item_separator`: the string that divides key/value pairs
            a.k.a. items in the list; it can be a single character or longer.
            It defaults to ``","``.
          - `key_terminators`: a string containing all single characters that
            are allowed to divide the key from the value.  Its default is
            ``":="``, so that you can use the colon *or* the equation sign for
            this.

        :type excerpt: `preprocessor.Excerpt`
        :type parent_element: `parser.Node`
        :type item_separator: unicode
        :type key_terminators: unicode

        :Exceptions:
          - `SettingUnknownKeyError`: raised if a key could not be added to the
            ``SettingsDict`` due to rules of closed section etc.
          - `SettingInvalidSectionError`: raised if a section could not be
            added because new sections are not allowed in this
            ``SettingsDict``.
          - `SettingInvalidKeyValueListError`: raised if the synatx of the
            key/value list was invalid

        Example:

            >>> from . import preprocessor, parser
            >>> excerpt = preprocessor.Excerpt("a:b, c = 4, d", "PRE",
            ...                                "myfile.bcat", {}, {})
            >>> settings = SettingsDict()
            >>> settings.set_default("a", None, "unicode")
            >>> settings.set_default("c", None, "int")
            >>> settings.set_default("d", False)
            >>> settings.close_section("")
            >>> settings.inhibit_new_sections()
            >>> settings.parse_keyvalue_list(excerpt, parser.Node(None))
            >>> settings
            {u'a': u'b', u'c': 4, u'd': True}
            >>> type(settings["c"])
            <type 'int'>
            >>> for key in settings.iterkeys(): print key.original_position()
            file "myfile.bcat", line 1, column 0
            file "myfile.bcat", line 1, column 5
            file "myfile.bcat", line 1, column 12

        """
        # In the current Bobcat source code, no warnings should happen here but
        # only errors.  But just to be sure, I convert all warnings to errors
        # nevertheless.
        warnings.simplefilter("error", SettingWarning)
        item_pattern = re.compile(ur"(?P<key>[-\w\s.@^!$%&/?*~#|><]+?)(?:[" +
                                  re.escape(key_terminators) +
                                  ur"](?P<value>.*?))?(?:(?:" + re.escape(item_separator) +
                                  ur"\s*)|\Z)", re.UNICODE | re.DOTALL)
        escaped_text = excerpt.escaped_text().rstrip()
        current_position = 0
        while current_position < len(escaped_text):
            next_item_match = item_pattern.match(escaped_text, current_position)
            if next_item_match:
                start, end = next_item_match.span("key")
                key = excerpt[start:end].apply_postprocessing().normalize_whitespace()
                if next_item_match.group("value") is not None:
                    start, end = next_item_match.span("value")
                    value = unicode(excerpt[start:end].apply_postprocessing()).strip()
                else:
                    value = u"true"
                try:
                    self.store_new_value(key, value, "keyval list")
                except (SettingUnknownKeyError, SettingInvalidSectionError), error:
                    if parent_element:
                        parent_element.throw_parse_warning(
                            "unknown key '%s'" % key, key.original_position())
                    else:
                        raise
                except SettingWrongTypeError, error:
                    if parent_element:
                        parent_element.throw_parse_warning(
                            "type of value for '%s' is wrong; expected %s but got %s" %
                            (key, error.previous_type, error.new_type),
                            key.original_position())
                    else:
                        raise
                current_position = next_item_match.end()
            else:
                erroneous_excerpt = excerpt[current_position:].apply_postprocessing().strip()
                if parent_element:
                    parent_element.throw_parse_error(
                        "invalid key--value syntax in '%s'" %
                        erroneous_excerpt, excerpt.original_position(current_position))
                    break
                else:
                    raise SettingInvalidKeyValueListError(erroneous_excerpt)
        warnings.resetwarnings()
            
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
        # pylint: disable-msg=R0912
        if isinstance(filenames, basestring):
            filenames = [filenames]
        read_files = []
        for filename in filenames:
            try:
                payload = open(filename).read()
                encoding = common.parse_local_variables(payload.splitlines()[0],
                                                        comment_marker="(#|;)").get("coding", "utf-8")
                payload_file = StringIO.StringIO(payload.decode(encoding))
            except UnicodeDecodeError:
                warnings.warn(SettingWarning(u"invalid encoding in file %s; "
                                             u"skipped this file" % filename), stacklevel=2)
                continue
            except IOError:
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
                        value = config_parser.get(section, option,
                                                  vars=self.predefined_variables).strip()
                        if section == "Paths":
                            value = os.path.abspath(os.path.expanduser(value))
                        self.store_new_value(key, value, source="conf file")
                    except ConfigParser.InterpolationMissingOptionError, error:
                        warnings.warn(SettingWarning(u"setting '%s' misses predefined "
                                                     u"variable '%s'" % (key, error.reference)))
                    except SettingError, error:
                        warnings.warn(SettingWarning(u'file "%s": ' % filename +
                                                     error.description), stacklevel=2)
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
    The absolute path to the Bobcat input filename.  Must be `None` if the input
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
settings.set_default("quiet", False, docstring="""
    If ``True``, all output to stdout and stderr is supressed.""")
