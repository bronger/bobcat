#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for `bobcatlib.settings`.

:var suite: the test suite which is exported by this module, to be used by a
  higher-level module for inclusion into a testing process.

:type suite: ``unittext.TextSuite``
"""

import unittest, doctest, os, warnings
from bobcatlib import settings, common

common.setup_logging()
settings.settings["quiet"] = True

suite = unittest.TestSuite()

class TestGetBoolean(unittest.TestCase):
    """Test case for `settings.Setting.get_boolean`.
    """
    def setUp(self):
        self.setting = settings.Setting(u"key", u"value")
    def test_on_off(self):
        """"on" and "off" should be converted correctly to boolean"""
        self.assertEqual(self.setting.get_boolean("on"), True)
        self.assertEqual(self.setting.get_boolean("off"), False)
    def test_true_false(self):
        """"true" and "false" should be converted correctly to boolean"""
        self.assertEqual(self.setting.get_boolean("true"), True)
        self.assertEqual(self.setting.get_boolean("false"), False)
    def test_boolean_input(self):
        """`True` and `False` should be converted correctly to boolean"""
        self.assertEqual(self.setting.get_boolean(True), True)
        self.assertEqual(self.setting.get_boolean(False), False)
    def test_yes_no(self):
        """"yes" and "no" should be converted correctly to boolean"""
        self.assertEqual(self.setting.get_boolean("yes"), True)
        self.assertEqual(self.setting.get_boolean("no"), False)
    def test_invalid_input(self):
        """upper-case "True" and other invalid input should raise an exception"""
        self.assertRaises(ValueError, lambda: self.setting.get_boolean("True"))
        self.assertRaises(ValueError, lambda: self.setting.get_boolean(1))
    def shortDescription(self):
        description = super(TestGetBoolean, self).shortDescription()
        return "settings.Setting.get_boolean: " + (description or "")

class TestDetectType(unittest.TestCase):
    """Test case for `settings.Setting.detect_type`.
    """
    def setUp(self):
        self.setting = settings.Setting(u"key", "value")
    def test_string_direct(self):
        """string input should be detected as "unicode" with source "direct"/"default\""""
        for source in ("direct", "default"):
            self.assertEqual(self.setting.detect_type(u"Hello", source), "unicode")
            self.assertEqual(self.setting.detect_type("Hello", source), "unicode")
    def test_int_direct(self):
        """int input should be detected as "int" with source "direct"/"default\""""
        for source in ("direct", "default"):
            self.assertEqual(self.setting.detect_type(1, source), "int")
    def test_float_direct(self):
        """float input should be detected as "float" with source "direct"/"default\""""
        for source in ("direct", "default"):
            self.assertEqual(self.setting.detect_type(3.14, source), "float")
    def test_bool_direct(self):
        """bool input should be detected as "bool" with source "direct"/"default\""""
        for source in ("direct", "default"):
            self.assertEqual(self.setting.detect_type(True, source), "bool")
    def test_list_direct(self):
        """list input should be detected properly with source "direct"/"default\""""
        for source in ("direct", "default"):
            self.assertEqual(self.setting.detect_type([1, 2, 3], source), "int")
            self.assertEqual(self.setting.detect_type([1, 2.3, 3], source), "int")
            self.assertEqual(self.setting.detect_type([1.0, 2.0, 3.0], source), "float")
            self.assertEqual(self.setting.detect_type([u"u", u"v", u"w"], source), "unicode")
            self.assertEqual(self.setting.detect_type([True, 2, 3], source), "bool")
    def test_empty_list(self):
        """empty list input should raise an exception"""
        self.assertRaises(settings.SettingError, lambda: self.setting.detect_type([], "direct"))
    def test_string_unpacking(self):
        """strings should be unpacked if source is "conf file" or "keyval list\""""
        for source in ["conf file", "keyval list"]:
            self.assertEqual(self.setting.detect_type(u"3.14", source), "float")
            self.assertEqual(self.setting.detect_type(u"-3.14", source), "float")
            self.assertEqual(self.setting.detect_type(u'"3.14"', source), "unicode")
            self.assertEqual(self.setting.detect_type(u"yes", source), "bool")
            self.assertEqual(self.setting.detect_type(u"True", source), "unicode")
    def test_string_list_unpacking(self):
        """strings containing lists should be unpacked if source is "conf file\""""
        self.assertEqual(self.setting.detect_type(u"(1.0, 2.0, 3.0)", "conf file"), "float")
        self.assertEqual(self.setting.detect_type(u"(1, 2, 3)", "conf file"), "int")
        self.assertEqual(self.setting.detect_type(u'("1", "2", "3")', "conf file"), "unicode")
    def test_string_list_unpacking_keyval_list(self):
        """strings containing lists should not be unpacked if source is "keyval list\""""
        self.assertEqual(self.setting.detect_type(u"(1.0, 2.0, 3.0)", "keyval list"), "unicode")
        self.assertEqual(self.setting.detect_type(u"(1, 2, 3)", "keyval list"), "unicode")
        self.assertEqual(self.setting.detect_type(u'("1", "2", "3")', "keyval list"), "unicode")
    def test_invalid_type(self):
        """Trying to detect an invalid type should fail"""
        self.assertRaises(settings.SettingError, lambda: self.setting.detect_type(None, "direct"))
        self.assertRaises(settings.SettingError, lambda: self.setting.detect_type({}, "direct"))
        # Maybe tuples should be handled like lists
#        self.assertRaises(settings.SettingError, lambda: self.setting.detect_type((), "direct"))
    def test_malformed_parentheses_syntax(self):
        """unmatched parentheses in list syntax should be interpreted as mere string"""
        self.assertEqual(self.setting.detect_type(u"(1, 2, 3]", "conf file"), "unicode")
    def shortDescription(self):
        description = super(TestDetectType, self).shortDescription()
        return "settings.Setting.detect_type: " + (description or "")

# In the following, some tests are marked as "spurious" because -- although
# they pass with the current implementation -- they are questionable.  The
# problem is that such things should never happen in the program, so actually,
# adjust_value_to_type should fail in these cases.  However, this is not too
# bad because the current behaviour is cleanly documented, and the called
# procedure does all checking to ensure that these cases never happen.
    
class TestAdjustValueToTypeInt(unittest.TestCase):
    """Test case for `settings.Setting.adjust_value_to_type`.  Here, only the
    case for converting to ``int`` is covered.
    """
    def setUp(self):
        self.setting = settings.Setting(u"key", 1)
    def test_adjust_string_direct_default(self):
        """with source direct/default, trying to adjust a string to int type should fail"""
        for source in ("direct", "default"):
            self.setting.value = u"hello"
            self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type(source))
# The following is a spurious test, see above
    def test_adjust_float_direct_default(self):
        """with source direct/default, trying to adjust a float to int should convert to int """ \
            """(spurious)"""
        for source in ("direct", "default"):
            self.setting.value = 2.1
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, int(2.1))
    def test_adjust_int_direct_default(self):
        """with source direct/default, trying to adjust an int to int should convert to int"""
        for source in ("direct", "default"):
            self.setting.value = 2
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, 2)
# The following is a spurious test, see above
    def test_adjust_bool_direct_default(self):
        """with source direct/default, trying to adjust a bool to int should convert to int """ \
            """(spurious)"""
        for source in ("direct", "default"):
            self.setting.value = True
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, 1)
# The following is a spurious test, see above
    def test_adjust_list_direct_default(self):
        """with source direct/default, trying to adjust a list of float to int should """ \
            """convert to list of int (spurious)"""
        for source in ("direct", "default"):
            self.setting.value = [1.3, 4.3, u"6"]
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, [int(1.3), int(4.3), int(u"6")])

    def test_non_string_conffile(self):
        """with source conf file, trying to adjust a non-string with "conf-file" should fail"""
        self.setting.value = 1
        self.assertRaises(AssertionError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_string_conffile(self):
        """with source conf file, trying to adjust a string to int type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_float_conffile(self):
        """with source conf file, trying to adjust a float to int should fail"""
        self.setting.value = u"2.1"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_int_conffile(self):
        """with source conf file, trying to adjust an int to int should convert to int"""
        self.setting.value = u"2"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, 2)
    def test_adjust_bool_conffile(self):
        """with source conf file, trying to adjust a bool to int should fail"""
        self.setting.value = u"true"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_list_conffile(self):
        """with source conf file, trying to adjust a list of int to int should convert """ \
            """to list of int"""
        self.setting.value = u'(1, 4, 6)'
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [1, 4, 6])
    def test_adjust_list_float_conffile(self):
        """with source conf file, trying to adjust a list of float to int should fail"""
        self.setting.value = u"(1.2, 4.4, 6.3)"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_list_mixed_conffile(self):
        """with source conf file, trying to adjust a list of mixed values to int should fail"""
        self.setting.value = u'(1, 4, "6")'
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))

    def test_non_string_keyval(self):
        """with source keyval list, trying to adjust a non-string should fail"""
        self.setting.value = 1
        self.assertRaises(AssertionError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_string_keyval(self):
        """with source keyval list, trying to adjust a string to int type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_float_keyval(self):
        """with source keyval list, trying to adjust a float to int should fail"""
        self.setting.value = u"2.1"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_int_keyval(self):
        """with source keyval list, trying to adjust an int to int should convert to int"""
        self.setting.value = u"2"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, 2)
    def test_adjust_bool_keyval(self):
        """with source keyval list, trying to adjust a bool to int should fail"""
        self.setting.value = u"true"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_list_keyval(self):
        """with source keyval list, trying to convert lists should fail"""
        self.setting.value = u'(1, 4, 6)'
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))

    def shortDescription(self):
        description = super(TestAdjustValueToTypeInt, self).shortDescription()
        return "settings.Setting.adjust_value_to_type: " + (description or "")
    
class TestAdjustValueToTypeFloat(unittest.TestCase):
    """Test case for `settings.Setting.adjust_value_to_type`.  Here, only the
    case for converting to ``float`` is covered.
    """
    def setUp(self):
        self.setting = settings.Setting(u"key", 3.14)
    def test_adjust_string_direct_default(self):
        """with source direct/default, trying to adjust a string to float type should fail"""
        for source in ("direct", "default"):
            self.setting.value = u"hello"
            self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type(source))
    def test_adjust_float_direct_default(self):
        """with source direct/default, trying to adjust a float to float should convert to float"""
        for source in ("direct", "default"):
            self.setting.value = 2.1
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, 2.1)
    def test_adjust_int_direct_default(self):
        """with source direct/default, trying to adjust an int to float should convert to float"""
        for source in ("direct", "default"):
            self.setting.value = 2
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, 2.0)
            self.assert_(isinstance(self.setting.value, float))
# The following is a spurious test, see above
    def test_adjust_bool_direct_default(self):
        """with source direct/default, trying to adjust a bool to float should convert to """ \
            """float (spurious)"""
        for source in ("direct", "default"):
            self.setting.value = True
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, 1.0)
            self.assert_(isinstance(self.setting.value, float))
# The following is a spurious test, see above
    def test_adjust_list_direct_default(self):
        """with source direct/default, trying to adjust a list of float to float should """ \
            """convert to list of float (spurious)"""
        for source in ("direct", "default"):
            self.setting.value = [1.3, 4.3, u"6"]
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, [1.3, 4.3, 6.0])

    def test_non_string_conffile(self):
        """with source conf file, trying to adjust a non-string with "conf-file" should fail"""
        self.setting.value = 1.0
        self.assertRaises(AssertionError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_string_conffile(self):
        """with source conf file, trying to adjust a string to float type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_float_conffile(self):
        """with source conf file, trying to adjust a float to float should convert to float"""
        self.setting.value = u"2.1"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, 2.1)
    def test_adjust_int_conffile(self):
        """with source conf file, trying to adjust an int to float should convert to float"""
        self.setting.value = u"2"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, 2.0)
        self.assert_(isinstance(self.setting.value, float))
    def test_adjust_bool_conffile(self):
        """with source conf file, trying to adjust a bool to float should fail"""
        self.setting.value = u"true"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_list_conffile(self):
        """with source conf file, trying to adjust a list of int to float should convert """ \
            """to list of float"""
        self.setting.value = u'(1, 4, 6)'
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [1.0, 4.0, 6.0])
    def test_adjust_list_float_conffile(self):
        """with source conf file, trying to adjust a list of float to float should convert """ \
            """to a list of float"""
        self.setting.value = u"(1.2, 4.4, 6.3)"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [1.2, 4.4, 6.3])
    def test_adjust_list_mixed_conffile(self):
        """with source conf file, trying to adjust a list of mixed values to float should fail"""
        self.setting.value = u'(1, 4, "6")'
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))

    def test_non_string_keyval(self):
        """with source keyval list, trying to adjust a non-string should fail"""
        self.setting.value = 1.0
        self.assertRaises(AssertionError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_string_keyval(self):
        """with source keyval list, trying to adjust a string to float type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_float_keyval(self):
        """with source keyval list, trying to adjust a float to float should convert to float"""
        self.setting.value = u"2.1"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, 2.1)
        self.assert_(isinstance(self.setting.value, float))
    def test_adjust_int_keyval(self):
        """with source keyval list, trying to adjust an int to float should convert to float"""
        self.setting.value = u"2"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, 2.0)
        self.assert_(isinstance(self.setting.value, float))
    def test_adjust_bool_keyval(self):
        """with source keyval list, trying to adjust a bool to float should fail"""
        self.setting.value = u"true"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_list_keyval(self):
        """with source keyval list, trying to convert lists should fail"""
        self.setting.value = u"(1.0, 4.2, 6.1)"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))

    def shortDescription(self):
        description = super(TestAdjustValueToTypeFloat, self).shortDescription()
        return "settings.Setting.adjust_value_to_type: " + (description or "")
    
class TestAdjustValueToTypeBool(unittest.TestCase):
    """Test case for `settings.Setting.adjust_value_to_type`.  Here, only the
    case for converting to ``bool`` is covered.
    """
    def setUp(self):
        self.setting = settings.Setting(u"key", True)
    def test_adjust_string_direct_default(self):
        """with source direct/default, trying to adjust a string to bool type should fail"""
        for source in ("direct", "default"):
            self.setting.value = u"hello"
            self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type(source))
    def test_adjust_float_direct_default(self):
        """with source direct/default, trying to adjust a float to bool should fail"""
        for source in ("direct", "default"):
            self.setting.value = 2.1
            self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type(source))
    def test_adjust_int_direct_default(self):
        """with source direct/default, trying to adjust an int to bool should fail"""
        for source in ("direct", "default"):
            self.setting.value = 2
            self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type(source))
    def test_adjust_bool_direct_default(self):
        """with source direct/default, trying to adjust a bool to bool should convert to bool"""
        for source in ("direct", "default"):
            self.setting.value = True
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, True)
    def test_adjust_list_direct_default(self):
        """with source direct/default, trying to adjust a list of bool to bool should """ \
            """convert to list of bool"""
        for source in ("direct", "default"):
            self.setting.value = [True, True, False]
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, [True, True, False])

    def test_non_string_conffile(self):
        """with source conf file, trying to adjust a non-string with "conf-file" should fail"""
        self.setting.value = True
        self.assertRaises(AssertionError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_string_conffile(self):
        """with source conf file, trying to adjust a string to bool type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_float_conffile(self):
        """with source conf file, trying to adjust a float to bool should fail"""
        self.setting.value = u"2.1"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_int_conffile(self):
        """with source conf file, trying to adjust an int to bool should fail"""
        self.setting.value = u"2"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_bool_conffile(self):
        """with source conf file, trying to adjust a bool to bool should convert to bool"""
        self.setting.value = u"false"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, False)
    def test_adjust_list_conffile(self):
        """with source conf file, trying to adjust a list of int to bool should fail"""
        self.setting.value = u'(1, 0, 6)'
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
# The following is a spurious test, see above
    def test_adjust_list_float_conffile(self):
        """with source conf file, trying to adjust a list of float to bool should convert """ \
            """to a list of bool (spurious)"""
        self.setting.value = u"(1.2, 4.4, 6.3)"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [True, True, True])
    def test_adjust_list_float_conffile(self):
        """with source conf file, trying to adjust a list of bool to bool should convert """ \
            """to a list of bool"""
        self.setting.value = u'(yes, yes, no)'
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [True, True, False])
    def test_adjust_list_mixed_conffile(self):
        """with source conf file, trying to adjust a list of mixed values to bool should fail"""
        self.setting.value = u'(1, 4, u"6")'
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))

    def test_non_string_keyval(self):
        """with source keyval list, trying to adjust a non-string should fail"""
        self.setting.value = False
        self.assertRaises(AssertionError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_string_keyval(self):
        """with source keyval list, trying to adjust a string to bool type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_float_keyval(self):
        """with source keyval list, trying to adjust a float to bool should fail"""
        self.setting.value = u"2.1"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_int_keyval(self):
        """with source keyval list, trying to adjust an int to bool should convert to bool"""
        self.setting.value = u"2"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_bool_keyval(self):
        """with source keyval list, trying to adjust a bool to bool should convert to bool"""
        self.setting.value = u"no"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, False)
    def test_adjust_list_keyval(self):
        """with source keyval list, trying to convert lists should fail"""
        self.setting.value = u"(1.0, 4.2, 6.1)"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))

    def shortDescription(self):
        description = super(TestAdjustValueToTypeBool, self).shortDescription()
        return "settings.Setting.adjust_value_to_type: " + (description or "")
    
class TestAdjustValueToTypeUnicode(unittest.TestCase):
    """Test case for `settings.Setting.adjust_value_to_type`.  Here, only the
    case for converting to ``unicode`` is covered.
    """
    def setUp(self):
        self.setting = settings.Setting(u"key", u"super")
    def test_adjust_string_direct_default(self):
        """with source direct/default, trying to adjust a string to string type should """ \
            """convert to string"""
        for source in ("direct", "default"):
            self.setting.value = u"hello"
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, u"hello")
# The following is a spurious test, see above
    def test_adjust_float_direct_default(self):
        """with source direct/default, trying to adjust a float to string should convert to """ \
            """string (spurious)"""
        for source in ("direct", "default"):
            self.setting.value = 2.1
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, u"2.1")
            self.assert_(isinstance(self.setting.value, unicode))
# The following is a spurious test, see above
    def test_adjust_int_direct_default(self):
        """with source direct/default, trying to adjust an int to string should convert to """ \
            """string (spurious)"""
        for source in ("direct", "default"):
            self.setting.value = 2
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, u"2")
            self.assert_(isinstance(self.setting.value, unicode))
# The following is a spurious test, see above
    def test_adjust_bool_direct_default(self):
        """with source direct/default, trying to adjust a bool to string should convert to """ \
            """string (spurious)"""
        for source in ("direct", "default"):
            self.setting.value = True
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, u"True")
            self.assert_(isinstance(self.setting.value, unicode))
# The following is a spurious test, see above
    def test_adjust_list_direct_default(self):
        """with source direct/default, trying to adjust a list of float to string should """ \
            """convert to list of string (spurious)"""
        for source in ("direct", "default"):
            self.setting.value = [1.3, 4.3, u"6"]
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, [u"1.3", u"4.3", u"6"])

    def test_adjust_string_conffile(self):
        """with source conf file, trying to adjust a string to string type should convert """ \
            """to string"""
        self.setting.value = u"hello"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, u"hello")
        self.assert_(isinstance(self.setting.value, unicode))
    def test_adjust_float_conffile(self):
        """with source conf file, trying to adjust a float to string should convert to string"""
        self.setting.value = u"2.1"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, u"2.1")
        self.assert_(isinstance(self.setting.value, unicode))
    def test_adjust_int_conffile(self):
        """with source conf file, trying to adjust an int to string should convert to string"""
        self.setting.value = u"2"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, u"2")
        self.assert_(isinstance(self.setting.value, unicode))
    def test_adjust_bool_conffile(self):
        """with source conf file, trying to adjust a bool to string should convert to string"""
        self.setting.value = u"true"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, u"true")
        self.assert_(isinstance(self.setting.value, unicode))
    def test_adjust_list_conffile(self):
        """with source conf file, trying to adjust a list of int to string should convert """ \
            """to list of string"""
        self.setting.value = u'(1, 4, 6)'
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [u"1", u"4", u"6"])
        for element in self.setting.value:
            self.assert_(isinstance(element, unicode))
    def test_adjust_list_float_conffile(self):
        """with source conf file, trying to adjust a list of float to string should convert """ \
            """to a list of string"""
        self.setting.value = u"(1.2, 4.4, 6.3)"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, ["1.2", u"4.4", u"6.3"])
        for element in self.setting.value:
            self.assert_(isinstance(element, unicode))
    def test_adjust_list_mixed_conffile(self):
        """with source conf file, trying to adjust a list of mixed values to string """\
            """should convert to list of string"""
        self.setting.value = u'(1, 4, "6")'
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [u"1", u"4", u"6"])
        for element in self.setting.value:
            self.assert_(isinstance(element, unicode))

    def test_adjust_string_keyval(self):
        """with source keyval list, trying to adjust a string to string type should """ \
            """convert to string"""
        self.setting.value = u"hello"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, u"hello")
        self.assert_(isinstance(self.setting.value, unicode))
    def test_adjust_float_keyval(self):
        """with source keyval list, trying to adjust a float to string should convert to string"""
        self.setting.value = u"2.1"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, u"2.1")
        self.assert_(isinstance(self.setting.value, unicode))
    def test_adjust_int_keyval(self):
        """with source keyval list, trying to adjust an int to string should convert to string"""
        self.setting.value = u"2"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, u"2")
        self.assert_(isinstance(self.setting.value, unicode))
    def test_adjust_bool_keyval(self):
        """with source keyval list, trying to adjust a bool to string should convert to string"""
        self.setting.value = u"true"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, u"true")
        self.assert_(isinstance(self.setting.value, unicode))
    def test_adjust_list_keyval(self):
        """with source keyval list, trying to convert lists should convert to string"""
        self.setting.value = u"(1.0, 4.2, 6.1)"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, u"(1.0, 4.2, 6.1)")
        self.assert_(isinstance(self.setting.value, unicode))

    def shortDescription(self):
        description = super(TestAdjustValueToTypeUnicode, self).shortDescription()
        return "settings.Setting.adjust_value_to_type: " + (description or "")

class TestAdjustValueToTypeInvalidSource(unittest.TestCase):
    """Test case for `settings.Setting.adjust_value_to_type`.  Here, I test for
    handling of an invalid source parameter.
    """
    def setUp(self):
        self.setting = settings.Setting(u"key", u"super")
    def test_invalid_source(self):
        """passing an invalid source should fail"""
        self.assertRaises(AssertionError, lambda: self.setting.adjust_value_to_type("foobar"))
    def shortDescription(self):
        description = super(TestAdjustValueToTypeInvalidSource, self).shortDescription()
        return "settings.Setting.adjust_value_to_type: " + (description or "")
    
class TestSetValueDefaultFirst(unittest.TestCase):
    """Test case for `settings.Setting.set_value`.  Here, I only test the case
    when a default value is set, and then a new value is set to override it."""
    def setUp(self):
        self.string_setting = settings.Setting(u"key", u"value", source="default")
        self.int_setting = settings.Setting(u"key", 1, source="default")
        self.float_setting = settings.Setting(u"key", 3.14, source="default")
        self.bool_setting = settings.Setting(u"key", True, source="default")
        self.list_setting = settings.Setting(u"key", [2, 3, -4], source="default")
    def assume_wrong_type_error(self, setting, value, source="direct"):
        """Called when a `settings.SettingWrongTypeError` is expected by
        setting a new value to the setting.

        :Parameters:
          - `setting`: the setting the value of which should be changed
          - `value`: the new value
          - `source`: the source, as used in `settings.Setting.set_value`

        :type setting: `settings.Setting`
        :type value: float, unicode, bool, int, or list
        :type source: str
        """
        self.assertRaises(settings.SettingWrongTypeError, lambda: setting.set_value(value, source))
    def assume_working_value_setting(self, setting, value, type_, source="direct",
                                     desired_value=None):
        """Called when a new value given to a setting is expected to work.

        :Parameters:
          - `setting`: the setting the value of which should be changed
          - `value`: the new value
          - `type_`: the expected new type after the assignment
          - `source`: the source, as used in `settings.Setting.set_value`
          - `desired_value`: The expected new value in the setting.  If not
            given, `value` itself is assumed.

        :type setting: `settings.Setting`
        :type value: float, unicode, bool, int, or list
        :type type_: type
        :type source: str
        :type desired_value: float, unicode, bool, int, or list
        """
        setting.set_value(value, source)
        self.assertEqual(setting.value, desired_value if desired_value is not None else value)
        self.assert_(isinstance(setting.value, type_))

    def test_double_default(self):
        """setting a default twice for a setting should fail"""
        self.assertRaises(AssertionError,
                          lambda: self.string_setting.set_value(u"hallo", "default"))
    def test_int_direct(self):
        """setting an int to a setting with source=direct should work or fail according to """ \
            """previous type"""
        self.assume_wrong_type_error(self.string_setting, 1)
        self.assume_working_value_setting(self.int_setting, 1, int)
        self.assume_working_value_setting(self.float_setting, 1, float)
        self.assume_wrong_type_error(self.bool_setting, 1)
        self.assume_working_value_setting(self.list_setting, 1, int)
    def test_float_direct(self):
        """setting a float to a setting with source=direct should work or fail according to """ \
            """previous type"""
        self.assume_wrong_type_error(self.string_setting, 3.2)
        self.assume_wrong_type_error(self.int_setting, 3.2)
        self.assume_working_value_setting(self.float_setting, 3.2, float)
        self.assume_wrong_type_error(self.bool_setting, 1)
        self.assume_wrong_type_error(self.list_setting, 3.2)
    def test_string_direct(self):
        """setting a string to a setting with source=direct should work or fail according to """ \
            """previous type"""
        self.assume_working_value_setting(self.string_setting, u"hallo", unicode)
        self.assume_working_value_setting(self.string_setting, u"yes", unicode)
        self.assume_working_value_setting(self.string_setting, u"1", unicode)
        self.assume_wrong_type_error(self.int_setting, u"hallo")
        self.assume_wrong_type_error(self.int_setting, u"1")
        self.assume_wrong_type_error(self.int_setting, u"yes")
        self.assume_wrong_type_error(self.float_setting, u"hallo")
        self.assume_wrong_type_error(self.float_setting, u"1")
        self.assume_wrong_type_error(self.float_setting, u"yes")
        self.assume_wrong_type_error(self.bool_setting, u"hallo")
        self.assume_wrong_type_error(self.bool_setting, u"1")
        self.assume_wrong_type_error(self.bool_setting, u"yes")
        self.assume_wrong_type_error(self.list_setting, u"hallo")
        self.assume_wrong_type_error(self.list_setting, u"1")
        self.assume_wrong_type_error(self.list_setting, u"yes")
    def test_bool_direct(self):
        """setting a bool to a setting with source=direct should work or fail according to """ \
            """previous type"""
        self.assume_wrong_type_error(self.string_setting, False)
        self.assume_wrong_type_error(self.int_setting, False)
        self.assume_wrong_type_error(self.float_setting, False)
        self.assume_working_value_setting(self.bool_setting, False, bool)
        self.assume_wrong_type_error(self.list_setting, False)
    def test_list_direct(self):
        """setting an list of int to a setting with source=direct should work or fail """ \
            """according to previous type"""
        self.assume_wrong_type_error(self.string_setting, [6, 3, 0])
        self.assume_working_value_setting(self.int_setting, [6, 3, 0], list)
        self.assume_working_value_setting(self.float_setting, [6, 3, 0], list)
        self.assume_wrong_type_error(self.bool_setting, [6, 3, 0])
        self.assume_working_value_setting(self.list_setting, [6, 3, 0], list)

    def test_nonstring_conffile_keyval(self):
        """setting ony other but a string with source="conf file"/"keyval list" should fail"""
        for source in ["conf file", "keyval list"]:
            self.assertRaises(AssertionError, lambda: self.int_setting.set_value(1, source))
            self.assertRaises(settings.SettingWrongTypeError,
                              lambda: self.int_setting.set_value(1.3, source))
            self.assertRaises(settings.SettingWrongTypeError,
                              lambda: self.int_setting.set_value(True, source))
            self.assertRaises(AssertionError,
                              lambda: self.int_setting.set_value([2, 4, -6], source))
    def test_int_conffile_keyval(self):
        """setting an int to a setting with source="conf file"/"keyval list" should """ \
            """work or fail according to previous type"""
        for source in ["conf file", "keyval list"]:
            self.assume_working_value_setting(self.string_setting, u"1", unicode, source)
            self.assume_working_value_setting(self.int_setting, u"1", int, source,
                                              desired_value=1)
            self.assume_working_value_setting(self.float_setting, u"1", float, source,
                                              desired_value=1.0)
            self.assume_wrong_type_error(self.bool_setting, u"1", source)
            self.assume_working_value_setting(self.list_setting, u"1", int, source,
                                              desired_value=1)
    def test_float_conffile_keyval(self):
        """setting a float to a setting with source="conf file"/"keyval list" should """ \
            """work or fail according to previous type"""
        for source in ["conf file", "keyval list"]:
            self.assume_working_value_setting(self.string_setting, u"3.2", unicode, source)
            self.assume_wrong_type_error(self.int_setting, u"3.2", source)
            self.assume_working_value_setting(self.float_setting, u"3.2", float, source,
                                              desired_value=3.2)
            self.assume_wrong_type_error(self.bool_setting, u"1", source)
            self.assume_wrong_type_error(self.list_setting, u"3.2", source)
    def test_string_conffile(self):
        """setting a string to a setting with source="conf file" should work or fail """ \
            """according to previous type"""
        self.assume_working_value_setting(self.string_setting, u'"hallo"', unicode, "conf file",
                                          desired_value=u"hallo")
        self.assume_working_value_setting(self.string_setting, u'"yes"', unicode, "conf file",
                                          desired_value=u"yes")
        self.assume_working_value_setting(self.string_setting, u'"1"', unicode, "conf file",
                                          desired_value=u"1")
        self.assume_wrong_type_error(self.int_setting, u'"hallo"', "conf file")
        self.assume_wrong_type_error(self.int_setting, u'"1"', "conf file")
        self.assume_wrong_type_error(self.int_setting, u'"yes"', "conf file")
        self.assume_wrong_type_error(self.float_setting, u'"hallo"', "conf file")
        self.assume_wrong_type_error(self.float_setting, u'"1"', "conf file")
        self.assume_wrong_type_error(self.float_setting, u'"yes"', "conf file")
        self.assume_wrong_type_error(self.bool_setting, u'"hallo"', "conf file")
        self.assume_wrong_type_error(self.bool_setting, u'"1"', "conf file")
        self.assume_wrong_type_error(self.bool_setting, u'"yes"', "conf file")
        self.assume_wrong_type_error(self.list_setting, u'"hallo"', "conf file")
        self.assume_wrong_type_error(self.list_setting, u'"1"', "conf file")
        self.assume_wrong_type_error(self.list_setting, u'"yes"', "conf file")
    def test_bool_conffile_keyval(self):
        """setting a bool to a setting with source="conf file"/"keyval list" should """ \
            """work or fail according to previous type"""
        for source in ["conf file", "keyval list"]:
            self.assume_working_value_setting(self.string_setting, u"no", unicode, source)
            self.assume_wrong_type_error(self.int_setting, u"no", source)
            self.assume_wrong_type_error(self.float_setting, u"no", source)
            self.assume_working_value_setting(self.bool_setting, u"no", bool, source,
                                              desired_value=False)
            self.assume_wrong_type_error(self.list_setting, u"no", source)
    def test_list_conffile(self):
        """setting a list of int to a setting with source="conf file" should work or fail """ \
            """according to previous type"""
        self.assume_working_value_setting(self.string_setting, u"(6, 3, 0)", list, "conf file",
                                          desired_value=[u"6", u"3", u"0"])
        self.assume_working_value_setting(self.int_setting, u"(6, 3, 0)", list, "conf file",
                                          desired_value=[6, 3, 0])
        self.assume_working_value_setting(self.float_setting, u"(6, 3, 0)", list, "conf file",
                                          desired_value=[6.0, 3.0, 0.0])
        self.assume_wrong_type_error(self.bool_setting, u"(6, 3, 0)", "conf file")
        self.assume_working_value_setting(self.list_setting, u"(6, 3, 0)", list, "conf file",
                                          desired_value=[6, 3, 0])

    def test_string_keyval(self):
        """setting a string to a setting with source="keyval list" should work or fail """ \
            """according to previous type"""
        self.assume_working_value_setting(self.string_setting, u'"hallo"', unicode, "keyval list")
        self.assume_working_value_setting(self.string_setting, u'"yes"', unicode, "keyval list")
        self.assume_working_value_setting(self.string_setting, u'"1"', unicode, "keyval list")
        self.assume_wrong_type_error(self.int_setting, u'"hallo"', "keyval list")
        self.assume_wrong_type_error(self.int_setting, u'"1"', "keyval list")
        self.assume_wrong_type_error(self.int_setting, u'"yes"', "keyval list")
        self.assume_wrong_type_error(self.float_setting, u'"hallo"', "keyval list")
        self.assume_wrong_type_error(self.float_setting, u'"1"', "keyval list")
        self.assume_wrong_type_error(self.float_setting, u'"yes"', "keyval list")
        self.assume_wrong_type_error(self.bool_setting, u'"hallo"', "keyval list")
        self.assume_wrong_type_error(self.bool_setting, u'"1"', "keyval list")
        self.assume_wrong_type_error(self.bool_setting, u'"yes"', "keyval list")
        self.assume_wrong_type_error(self.list_setting, u'"hallo"', "keyval list")
        self.assume_wrong_type_error(self.list_setting, u'"1"', "keyval list")
        self.assume_wrong_type_error(self.list_setting, u'"yes"', "keyval list")
    def test_list_keyval(self):
        """setting a list of int to a setting with source="keyval list" should work as string"""
        self.assume_working_value_setting(self.string_setting, u"(6, 3, 0)", unicode, "keyval list")
        self.assume_wrong_type_error(self.int_setting, u"(6, 3, 0)", "keyval list")
        self.assume_wrong_type_error(self.float_setting, u"(6, 3, 0)", "keyval list")
        self.assume_wrong_type_error(self.bool_setting, u"(6, 3, 0)", "keyval list")
        self.assume_wrong_type_error(self.list_setting, u"(6, 3, 0)", "keyval list")

    def shortDescription(self):
        description = super(TestSetValueDefaultFirst, self).shortDescription()
        return "settings.Setting.set_value with default first: " + (description or "")

class TestSetValueDefaultSecondDirect(unittest.TestCase):
    """Test case for `settings.Setting.set_value`, for the case that _first_,
    the settings gets a value, and _then_, a default value is given.

    In this use case, the original value was given with ``source="direct"``.
    """
    def setUp(self):
        self.string_setting = settings.Setting(u"key", u"value")
        self.int_setting = settings.Setting(u"key", 1)
        self.float_setting = settings.Setting(u"key", 3.14)
        self.bool_setting = settings.Setting(u"key", True)
        self.list_setting = settings.Setting(u"key", [2, 3, -4])
    def assume_wrong_type_error(self, setting, value):
        """Called when a `settings.SettingWrongTypeError` is expected by
        setting a default value to the setting.

        :Parameters:
          - `setting`: the setting the value of which should be changed
          - `value`: the new value

        :type setting: `settings.Setting`
        :type value: float, unicode, bool, int, or list
        """
        self.assertRaises(settings.SettingWrongTypeError,
                          lambda: setting.set_value(value, "default"))
    def assume_working_value_setting(self, setting, value, type_, desired_value=None):
        """Called when a default value given to a setting is expected to work.

        :Parameters:
          - `setting`: the setting the value of which should be changed
          - `value`: the new value
          - `type_`: the expected new type after the assignment
          - `desired_value`: The expected new value in the setting.  If not
            given, `value` itself is assumed.

        :type setting: `settings.Setting`
        :type value: float, unicode, bool, int, or list
        :type desired_value: float, unicode, bool, int, or list
        """
        old_value = setting.value
        setting.set_value(value, "default")
        self.assertEqual(setting.value, desired_value if desired_value is not None else old_value)
        self.assert_(isinstance(setting.value, type_))
    def test_string(self):
        """setting a string default should work or fail depending of previous type"""
        self.assume_working_value_setting(self.string_setting, u"3", unicode)
        self.assume_wrong_type_error(self.int_setting, u"3")
        self.assume_wrong_type_error(self.float_setting, u"3")
        self.assume_wrong_type_error(self.bool_setting, u"3")
        if self.list_setting:
            self.assume_wrong_type_error(self.list_setting, u"3")
    def test_int(self):
        """setting an int default should work or fail depending of previous type"""
        self.assume_wrong_type_error(self.string_setting, 1)
        self.assume_working_value_setting(self.int_setting, 1, int)
        self.assume_wrong_type_error(self.float_setting, 1)
        self.assume_wrong_type_error(self.bool_setting, 1)
        if self.list_setting:
            self.assume_working_value_setting(self.list_setting, 1, list)
    def test_float(self):
        """setting a float default should work or fail depending of previous type"""
        self.assume_wrong_type_error(self.string_setting, 3.24)
        self.assume_working_value_setting(self.int_setting, 3.24, float)
        self.assume_working_value_setting(self.float_setting, 3.24, float)
        self.assume_wrong_type_error(self.bool_setting, 3.24)
        if self.list_setting:
            self.assume_working_value_setting(self.list_setting, 3.24, list, [2.0, 3.0, -4.0])
    def test_bool(self):
        """setting a bool default should work or fail depending of previous type"""
        self.assume_wrong_type_error(self.string_setting, False)
        self.assume_wrong_type_error(self.int_setting, False)
        self.assume_wrong_type_error(self.float_setting, False)
        self.assume_working_value_setting(self.bool_setting, False, bool)
        if self.list_setting:
            self.assume_wrong_type_error(self.list_setting, False)
    def test_list(self):
        """setting a list of int default should work or fail depending of previous type"""
        self.assume_wrong_type_error(self.string_setting, [6, -3, 0])
        self.assume_working_value_setting(self.int_setting, [6, -3, 0], int)
        self.assume_wrong_type_error(self.float_setting, [6, -3, 0])
        self.assume_wrong_type_error(self.bool_setting, [6, -3, 0])
        if self.list_setting:
            self.assume_working_value_setting(self.list_setting, [6, -3, 0], list, [2, 3, -4])
    def shortDescription(self):
        description = super(TestSetValueDefaultSecondDirect, self).shortDescription()
        return 'settings.Setting.set_value with default first, source="direct": ' + \
            (description or "")

class TestSetValueDefaultSecondConf(TestSetValueDefaultSecondDirect):
    """Test case for `settings.Setting.set_value`, for the case that _first_,
    the settings gets a value, and _then_, a default value is given.

    In this use case, the original value was given with ``source="config
    file"``.
    """
    def setUp(self):
        self.string_setting = settings.Setting(u"key", u"value", source="conf file")
        self.int_setting = settings.Setting(u"key", u"2", source="conf file")
        self.float_setting = settings.Setting(u"key", u"3.14", source="conf file")
        self.bool_setting = settings.Setting(u"key", u"yes", source="conf file")
        self.list_setting = settings.Setting(u"key", u"(2, 3, -4)", source="conf file")
    def test_string(self):
        """setting a string default should work or fail depending of previous type"""
        self.assume_working_value_setting(self.string_setting, u"3", unicode)
        self.assume_working_value_setting(self.int_setting, u"3", unicode, u"2")
        self.assume_working_value_setting(self.float_setting, u"3", unicode, u"3.14")
        self.assume_working_value_setting(self.bool_setting, u"3", unicode, u"yes")
        self.assume_working_value_setting(self.list_setting, u"3", list, [u"2", u"3", u"-4"])
    def shortDescription(self):
        description = super(TestSetValueDefaultSecondConf, self).shortDescription()
        return 'settings.Setting.set_value with default first, source="conf file": ' + \
            (description or "")

class TestSetValueDefaultSecondKeyval(TestSetValueDefaultSecondDirect):
    """Test case for `settings.Setting.set_value`, for the case that _first_,
    the settings gets a value, and _then_, a default value is given.

    In this use case, the original value was given with ``source="keyval
    list"``.
    """
    def setUp(self):
        self.string_setting = settings.Setting(u"key", u"value", source="keyval list")
        self.int_setting = settings.Setting(u"key", u"2", source="keyval list")
        self.float_setting = settings.Setting(u"key", u"3.14", source="keyval list")
        self.bool_setting = settings.Setting(u"key", u"yes", source="keyval list")
        self.list_setting = None
    def test_string(self):
        """setting a string default should work or fail depending of previous type"""
        self.assume_working_value_setting(self.string_setting, u"3", unicode)
        self.assume_working_value_setting(self.int_setting, u"3", unicode, u"2")
        self.assume_working_value_setting(self.float_setting, u"3", unicode, u"3.14")
        self.assume_working_value_setting(self.bool_setting, u"3", unicode, u"yes")
    def test_string_list(self):
        """setting a string default should leave a previous value with list syntax unchanged"""
        list_setting = settings.Setting(u"key", u"(2, 3, -4)", source="keyval list")
        self.assume_working_value_setting(list_setting, u"3", unicode, u"(2, 3, -4)")
    def shortDescription(self):
        description = super(TestSetValueDefaultSecondKeyval, self).shortDescription()
        return 'settings.Setting.set_value with default first, source="keyval list": ' + \
            (description or "")

class TestSetValueMisc(unittest.TestCase):
    """Test case for `settings.Setting.set_value`.  Here, I test for rim cases
    that can be considered pretty exotic.
    """
    def test_direct_after_conf(self):
        """after an initialization from a config file, setting a value to a
        string with source="direct" should work"""
        setting = settings.Setting(u"key", u"3", source="conf file")
        setting.set_value(u"Hallo")
        self.assertEqual(setting.value, u"Hallo")
    def test_direct_after_conf_after_direct(self):
        """after initialization with an int, a new value may be read from a
        config file, but now re-setting it with a string should fail"""
        setting = settings.Setting(u"key", 3)
        setting.set_value(u"3", source="conf file")
        self.assertRaises(settings.SettingWrongTypeError, lambda: setting.set_value(u"Hallo"))
        self.assertEqual(setting.value, 3)
    def test_default_after_direct_after_conf(self):
        """after an initialization from a config file, setting a value to a
        string, and then giving it an int default value should fail"""
        setting = settings.Setting(u"key", u"3", source="conf file")
        setting.set_value(u"3")
        self.assertRaises(settings.SettingWrongTypeError, lambda: setting.set_value(4, "default"))
        self.assertEqual(setting.value, u"3")
    def test_default_after_direct_after_conf2(self):
        """after an initialization from a config file, setting a value to an
        int and then giving it a string default value should fail"""
        setting = settings.Setting(u"key", u"3", source="conf file")
        setting.set_value(3)
        self.assertRaises(settings.SettingWrongTypeError, lambda: setting.set_value(u"4", "default"))
        self.assertEqual(setting.value, 3)
    def test_default_after_direct_after_keyval(self):
        """after an initialization from a key/value list and re-reading from a
        key/value list, setting the value to a string should work"""
        setting = settings.Setting(u"key", u"3", source="keyval list")
        setting.set_value(u"3", "keyval list")
        setting.set_value(u"3")
        self.assertEqual(setting.value, u"3")
        self.assert_(isinstance(setting.value, unicode))
    def shortDescription(self):
        description = super(TestSetValueMisc, self).shortDescription()
        return "settings.Setting.set_value: " + (description or "")

class TestSettingInit(unittest.TestCase):
    """Test case for `settings.Setting.__init__`.  I test the correct
    auto-detection of types here, and invalid parameter values."""
    def assume_working_instantiation(self, value, type_, source="direct", desired_value=None):
        """Called for instantiation a new setting and looking whether the
        auto-detection has worked.

        :Parameters:
          - `value`: the new value
          - `type_`: the expected new type after the instantiation
          - `source`: the source, as used in `settings.Setting.set_value`
          - `desired_value`: The expected new value in the setting.  If not
            given, `value` itself is assumed.

        :type value: float, unicode, bool, int, or list
        :type type_: type
        :type source: str
        :type desired_value: float, unicode, bool, int, or list
        """
        setting = settings.Setting(u"key", value, source=source)
        self.assertEqual(setting.value, desired_value if desired_value is not None else value)
        self.assert_(isinstance(setting.value, type_))
    def test_auto_detection_int(self):
        """int values should be properly auto-detected"""
        self.assume_working_instantiation(1, int)
    def test_auto_detection_float(self):
        """float values should be properly auto-detected"""
        self.assume_working_instantiation(1.0, float)
    def test_auto_detection_bool(self):
        """bool values should be properly auto-detected"""
        self.assume_working_instantiation(False, bool)
    def test_auto_detection_string(self):
        """string values should be properly auto-detected"""
        self.assume_working_instantiation(u"", unicode)
        self.assume_working_instantiation(u"no", unicode)
        self.assume_working_instantiation(u"1", unicode)
    def test_auto_detection_conf_keyval(self):
        """string values from configuration files and key/value lists should be properly """ \
            """auto-detected"""
        for source in ["conf file", "keyval list"]:
            self.assume_working_instantiation(u"", unicode, source)
            self.assume_working_instantiation(u"no", bool, source, False)
            self.assume_working_instantiation(u"1", int, source, 1)
            self.assume_working_instantiation(u"1.", float, source, 1.0)
            self.assume_working_instantiation(u"2.0", float, source, 2.0)
            self.assume_working_instantiation(u"-2.3e-16", float, source, -2.3e-16)
    def test_auto_detection_conf_special_syntax(self):
        """string values with the special list and string syntax from configuration files """ \
            """should be properly auto-detected"""
        self.assume_working_instantiation(u'"1"', unicode, "conf file", u"1")
        self.assume_working_instantiation(u"(1, 2, 3)", list, "conf file", [1, 2, 3])
        self.assume_working_instantiation(u'("1", "2", "3")', list, "conf file",
                                          [u"1", u"2", u"3"])
    def test_auto_detection_keyval_special_syntax(self):
        """string values with the special list and string syntax from key/value lists """ \
            """should remain as is"""
        self.assume_working_instantiation(u'"1"', unicode, "keyval list")
        self.assume_working_instantiation(u"(1, 2, 3)", unicode, "keyval list")
        self.assume_working_instantiation(u'("1", "2", "3")', unicode, "keyval list")
    def test_invalid_source(self):
        """passing an invalid source parameter should fail"""
        self.assertRaises(AssertionError, lambda: settings.Setting(u"key", 1, source="tralala"))
    def test_invalid_explicit_type(self):
        """passing an invalid explicit type parameter should fail"""
        self.assertRaises(AssertionError,
                          lambda: settings.Setting(u"key", 1, explicit_type="tralala"))
    def shortDescription(self):
        description = super(TestSettingInit, self).shortDescription()
        return "settings.Setting.__init__: " + (description or "")

class TestSettingInitExplicitType(unittest.TestCase):
    """Test case for constructing `settings.Setting` objects with an explicit
    type argument.

    All of these tests have to be considered spurious as those for
    ``adjust_value_to_type`` above.  Maybe it would be a good decision to drop
    the ``explicit_type`` argument completely.
    """
    def test_explicit_type_unicode(self):
        """giving an explicit type argument should work always for "unicode\""""
        setting = settings.Setting(u"key", [1, 2, 3], "unicode")
        self.assertEqual(setting.value, [u"1", u"2", u"3"])
        setting = settings.Setting(u"key", u"(1, 2, 3)", "unicode", source="conf file")
        self.assertEqual(setting.value, [u"1", u"2", u"3"])
    def test_explicit_type_bool(self):
        """giving an explicit type argument should work or fail for "bool" depending on """ \
            """whether it is exactly a bool string or not"""
        self.assertRaises(ValueError, lambda: settings.Setting(u"key", u"un", "bool"))
        self.assertRaises(ValueError, lambda: settings.Setting(u"key", 1, "bool"))
        setting = settings.Setting(u"key", True, "bool")
        self.assertEqual(setting.value, True)
        setting = settings.Setting(u"key", u"no", "bool")
        self.assertEqual(setting.value, False)
    def test_explicit_type_int(self):
        """giving an explicit type argument should work or fail for "int" depending on """ \
            """whether or not it can be converted"""
        self.assertRaises(ValueError, lambda: settings.Setting(u"key", u"1.0", "int"))
        setting = settings.Setting(u"key", False, "int")
        self.assertEqual(setting.value, 0)
        setting = settings.Setting(u"key", 1, "int")
        self.assertEqual(setting.value, 1)
        setting = settings.Setting(u"key", u"1", "int")
        self.assertEqual(setting.value, 1)
    def test_explicit_type_float(self):
        """giving an explicit type argument should work or fail for "float" depending on """ \
            """whether or not it can be converted"""
        self.assertRaises(ValueError, lambda: settings.Setting(u"key", "un", "float"))
        setting = settings.Setting(u"key", 1, "float")
        self.assertEqual(setting.value, 1.0)
        self.assert_(isinstance(setting.value, float))
        setting = settings.Setting(u"key", True, "float")
        self.assertEqual(setting.value, 1.0)
        self.assertRaises(ValueError, lambda: settings.Setting(u"key", u"no", "float"))
    def shortDescription(self):
        description = super(TestSettingInitExplicitType, self).shortDescription()
        return "settings.Setting.__init__ with explicit type argument (spurious): " + \
            (description or "")

class TestSettingsDict(unittest.TestCase):
    def test_loading_from_conf_file(self):
        """Loading a configuration file into a settings dictionary should work"""
        os.environ["HOME"] = "/home/user"
        settings_dict = settings.SettingsDict()
        settings_dict.set_default("General.quiet", True)
        settings_dict.set_predefined_variable("rootdir", "~/src/bobcat/")
        self.assertEqual(settings_dict.load_from_files("test.conf"), [u"test.conf"])
        self.assertEqual(settings_dict, {u'Veröffentlichung.supi': u'toll',
                                         u'Paths.backends': u'/home/user/src/bobcat/src/backends',
                                         u'General.quiet': True})
    def shortDescription(self):
        description = super(TestSettingsDict, self).shortDescription()
        return "settings.SettingsDict: " + (description or "")

class TestSettingsDictTestForClosedSection(unittest.TestCase):
    def setUp(self):
        self.settings = settings.SettingsDict()
        self.settings.set_default(u"General.quiet", True)
        self.settings.close_section(u"General")
        self.settings.set_predefined_variable("rootdir", "~/src/bobcat/")
        self.assertEqual(self.settings.load_from_files("test.conf"), [u"test.conf"])
    def test_add_to_non_closed_section(self):
        """Adding known keys to an unknown, non-closed section should work"""
        self.settings.test_for_closed_section("Unknown.section.quiet", False)
    def test_add_known_option_to_closed_section(self):
        """Adding known keys to a closed section should fail"""
        self.assertRaises(settings.SettingUnknownKeyError,
                          lambda: self.settings.test_for_closed_section(u"General.quiet", False))
    def test_add_unknown_option_to_closed_section(self):
        """Adding unknown keys to a closed section should fail"""
        self.assertRaises(settings.SettingUnknownKeyError,
                          lambda: self.settings.test_for_closed_section(u"General.quite", False))
    def shortDescription(self):
        description = super(TestSettingsDictTestForClosedSection, self).shortDescription()
        return "settings.SettingsDict.test_for_closed_section: " + (description or "")
    
class TestSettingsDictSetDefault(unittest.TestCase):
    def setUp(self):
        warnings.simplefilter("error")
        self.settings = settings.SettingsDict()
        self.settings.set_default(u"General.a", u"Hallo")
        self.settings.set_default(u"General.b", u"on")
        self.settings.set_default(u"General.c", 1)
        self.settings.set_default(u"General.d", 4.5)
        self.settings.set_default(u"General.e", None, u"unicode")
    def test_default_setting(self):
        """setting defaults should work"""
        self.assertEqual(self.settings, {u"General.c": 1, u"General.b": u"on", u"General.a": u"Hallo",
                                         u"General.e": None, u"General.d": 4.5})
    def test_set_wrong_type(self):
        """setting a value with another type than its default should fail"""
        def assignment():
            self.settings[u"General.b"] = True
        self.assertRaises(settings.SettingWrongTypeError, assignment)
    def test_set_unknown_option(self):
        """setting an unknown option should work"""
        self.settings[u"General.quiet"] = True
        self.assertEqual(self.settings["General.quiet"], True)
    def test_set_close_section_with_unknown_key(self):
        """closing a section with an option without default should fail """
        self.settings[u"General.quiet"] = True
        self.assertRaises(settings.SettingWarning, lambda: self.settings.close_section(u"General"))
    def test_add_new_key_to_closed_section(self):
        """adding an unknown key to a closed section should fail"""
        def assignment():
            self.settings[u"General.f"] = u"offf"
        self.settings.close_section(u"General")
        self.assertRaises(settings.SettingUnknownKeyError, assignment)
    def test_add_invalid_key(self):
        """adding an invalid key should fail"""
        def assignment():
            self.settings[u"General."] = u"offf"        
        self.assertRaises(AssertionError, assignment)
    def test_add_default_to_closed_section(self):
        """setting a new default in a closed section should fail"""
        self.settings.close_section(u"General")
        self.assertRaises(settings.SettingUnknownKeyError,
                          lambda: self.settings.set_default(u"General.f", [1,2,3,4]))
    def tearDown(self):
        warnings.resetwarnings()
    def shortDescription(self):
        description = super(TestSettingsDictSetDefault, self).shortDescription()
        return "settings.SettingsDict.set_default: " + (description or "")


class TestSettingsDictInhibitNewSections(unittest.TestCase):
    def setUp(self):
        self.settings = settings.SettingsDict()
        self.settings.set_default("General.quiet", True)
        self.settings.inhibit_new_sections()
    def test_set_default_in_known_section(self):
        """setting a new default in a known section should work"""
        self.settings.set_default(u"General.outfile", None, "unicode")
        self.assertEqual(self.settings[u"General.outfile"], None)
    def test_open_new_section(self):
        """opening a new section should fail"""
        self.assertRaises(settings.SettingInvalidSectionError,
                          lambda: self.settings.set_default(u"Newsection.outfile", None, "unicode"))
    def test_add_sectionless_key(self):
        """adding a sectionless option should fail"""
        def assignment():
            self.settings[u"sectionlesskey"] = 0
        self.assertRaises(settings.SettingInvalidSectionError, assignment)
    def shortDescription(self):
        description = super(TestSettingsDictInhibitNewSections, self).shortDescription()
        return "settings.SettingsDict.inhibit_new_sections: " + (description or "")

class TestSettingsDictParseKeyvalueList(unittest.TestCase):
    def setUp(self):
        from bobcatlib import preprocessor, parser
        self.excerpt = preprocessor.Excerpt(u"a:b, c = 4, d", "PRE", "myfile.rsl", {}, {})
        self.settings = settings.SettingsDict()
        self.settings.set_default(u"a", None, "unicode")
        self.settings.set_default(u"c", None, "int")
        self.settings.set_default(u"d", False)
        self.settings.close_section(u"")
        self.settings.inhibit_new_sections()
        self.settings.parse_keyvalue_list(self.excerpt, parser.Node(None))
    def test_parsing(self):
        """parsing of a key/value list should work"""
        self.assertEqual(self.settings, {u"a": u"b", u"c": 4, u"d": True})
        self.assert_(isinstance(self.settings[u"c"], int))
        self.assertEqual([key.original_position() for key in self.settings.iterkeys()],
                         [common.PositionMarker("myfile.rsl", 1, 0, 0),
                          common.PositionMarker("myfile.rsl", 1, 5, 0),
                          common.PositionMarker("myfile.rsl", 1, 12, 0)])
    def test_wrong_syntax(self):
        """parsing key/value lists with invalid syntax should fail"""
        from bobcatlib import preprocessor, parser
        self.excerpt = preprocessor.Excerpt(u"a(:b, c = 4, d", "PRE", "myfile.rsl", {}, {})
        self.assertRaises(settings.SettingInvalidKeyValueListError,
                          lambda: self.settings.parse_keyvalue_list(self.excerpt))
    def test_invalid_section(self):
        """parsing key/value lists with a new section where new sections are not allowed """ \
            """should fail"""
        from bobcatlib import preprocessor, parser
        self.excerpt = preprocessor.Excerpt(u"a.wrong:b, c = 4, d", "PRE", "myfile.rsl", {}, {})
        self.assertRaises(settings.SettingInvalidSectionError,
                          lambda: self.settings.parse_keyvalue_list(self.excerpt))
    def test_invalid_key(self):
        """parsing key/value lists with a new key in a closed section should fail"""
        from bobcatlib import preprocessor, parser
        self.excerpt = preprocessor.Excerpt(u"wrong:b, c = 4, d", "PRE", "myfile.rsl", {}, {})
        self.assertRaises(settings.SettingUnknownKeyError,
                          lambda: self.settings.parse_keyvalue_list(self.excerpt))
    def shortDescription(self):
        description = super(TestSettingsDictParseKeyvalueList, self).shortDescription()
        return "settings.SettingsDict.parse_keyvalue_list: " + (description or "")
    
for test_class in (TestGetBoolean, TestDetectType, TestAdjustValueToTypeInt,
                   TestAdjustValueToTypeFloat, TestAdjustValueToTypeBool,
                   TestAdjustValueToTypeUnicode, TestAdjustValueToTypeInvalidSource,
                   TestSetValueDefaultFirst,
                   TestSetValueDefaultSecondDirect,
                   TestSetValueDefaultSecondConf,
                   TestSetValueDefaultSecondKeyval,
                   TestSetValueMisc, TestSettingInit, TestSettingInitExplicitType,
                   TestSettingsDict, TestSettingsDictTestForClosedSection,
                   TestSettingsDictSetDefault,
                   TestSettingsDictInhibitNewSections, TestSettingsDictParseKeyvalueList):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))
