#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for `bobcatlib.settings`.

:var suite: the test suite which is exported by this module, to be used by a
  higher-level module for inclusion into a testing process.

:type suite: ``unittext.TextSuite``
"""

import unittest, doctest
from bobcatlib import settings

suite = unittest.TestSuite()

class TestGetBoolean(unittest.TestCase):
    """Test case for `settings.Setting.get_boolean`.
    """
    def setUp(self):
        self.setting = settings.Setting("key", "value")
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
        self.setting = settings.Setting("key", "value")
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
            self.assertEqual(self.setting.detect_type("3.14", source), "float")
            self.assertEqual(self.setting.detect_type("-3.14", source), "float")
            self.assertEqual(self.setting.detect_type('"3.14"', source), "unicode")
            self.assertEqual(self.setting.detect_type("yes", source), "bool")
            self.assertEqual(self.setting.detect_type("True", source), "unicode")
    def test_string_list_unpacking(self):
        """strings containing lists should be unpacked if source is "conf file\""""
        self.assertEqual(self.setting.detect_type("(1.0, 2.0, 3.0)", "conf file"), "float")
        self.assertEqual(self.setting.detect_type("(1, 2, 3)", "conf file"), "int")
        self.assertEqual(self.setting.detect_type('("1", "2", "3")', "conf file"), "unicode")
    def test_string_list_unpacking_keyval_list(self):
        """strings containing lists should not be unpacked if source is "keyval list\""""
        self.assertEqual(self.setting.detect_type("(1.0, 2.0, 3.0)", "keyval list"), "unicode")
        self.assertEqual(self.setting.detect_type("(1, 2, 3)", "keyval list"), "unicode")
        self.assertEqual(self.setting.detect_type('("1", "2", "3")', "keyval list"), "unicode")
    def test_invalid_type(self):
        """Trying to detect an invalid type should fail"""
        self.assertRaises(settings.SettingError, lambda: self.setting.detect_type(None, "direct"))
        self.assertRaises(settings.SettingError, lambda: self.setting.detect_type({}, "direct"))
        # Maybe tuples should be handled like lists
#        self.assertRaises(settings.SettingError, lambda: self.setting.detect_type((), "direct"))
    def test_malformed_parentheses_syntax(self):
        """unmatched parentheses in list syntax should be interpreted as mere string"""
        self.assertEqual(self.setting.detect_type("(1, 2, 3]", "conf file"), "unicode")
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
    def setUp(self):
        self.setting = settings.Setting("key", 1)
    def test_adjust_string_direct_default(self):
        """with source direct/default, trying to adjust a string to int type should fail"""
        for source in ("direct", "default"):
            self.setting.value = u"hello"
            self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type(source))
# The following is a spurious test, see above
    def test_adjust_float_direct_default(self):
        """with source direct/default, trying to adjust a float to int should convert to int"""
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
        """with source direct/default, trying to adjust a bool to int should convert to int"""
        for source in ("direct", "default"):
            self.setting.value = True
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, 1)
# The following is a spurious test, see above
    def test_adjust_list_direct_default(self):
        """with source direct/default, trying to adjust a list of float to int should """ \
            """convert to list of int"""
        for source in ("direct", "default"):
            self.setting.value = [1.3, 4.3, "6"]
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, [int(1.3), int(4.3), int("6")])

    def test_non_string_conffile(self):
        """with source conf file, trying to adjust a non-string with "conf-file" should fail"""
        self.setting.value = 1
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_string_conffile(self):
        """with source conf file, trying to adjust a string to int type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_float_conffile(self):
        """with source conf file, trying to adjust a float to int should fail"""
        self.setting.value = "2.1"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_int_conffile(self):
        """with source conf file, trying to adjust an int to int should convert to int"""
        self.setting.value = "2"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, 2)
    def test_adjust_bool_conffile(self):
        """with source conf file, trying to adjust a bool to int should fail"""
        self.setting.value = "true"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_list_conffile(self):
        """with source conf file, trying to adjust a list of int to int should convert """ \
            """to list of int"""
        self.setting.value = '(1, 4, 6)'
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [1, 4, 6])
    def test_adjust_list_float_conffile(self):
        """with source conf file, trying to adjust a list of float to int should fail"""
        self.setting.value = "(1.2, 4.4, 6.3)"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_list_mixed_conffile(self):
        """with source conf file, trying to adjust a list of mixed values to int should fail"""
        self.setting.value = '(1, 4, "6")'
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))

    def test_non_string_keyval(self):
        """with source keyval list, trying to adjust a non-string with "keyval list" should fail"""
        self.setting.value = 1
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_string_keyval(self):
        """with source keyval list, trying to adjust a string to int type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_float_keyval(self):
        """with source keyval list, trying to adjust a float to int should fail"""
        self.setting.value = "2.1"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_int_keyval(self):
        """with source keyval list, trying to adjust an int to int should convert to int"""
        self.setting.value = "2"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, 2)
    def test_adjust_bool_keyval(self):
        """with source keyval list, trying to adjust a bool to int should fail"""
        self.setting.value = "true"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_list_keyval(self):
        """with source keyval list, trying to convert lists should fail"""
        self.setting.value = '(1, 4, 6)'
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))

    def shortDescription(self):
        description = super(TestAdjustValueToTypeInt, self).shortDescription()
        return "settings.Setting.adjust_value_to_type: " + (description or "")
    
class TestAdjustValueToTypeFloat(unittest.TestCase):
    def setUp(self):
        self.setting = settings.Setting("key", 3.14)
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
        """with source direct/default, trying to adjust a bool to float should convert to float"""
        for source in ("direct", "default"):
            self.setting.value = True
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, 1.0)
            self.assert_(isinstance(self.setting.value, float))
    def test_adjust_list_direct_default(self):
        """with source direct/default, trying to adjust a list of float to float should """ \
            """convert to list of float"""
        for source in ("direct", "default"):
            self.setting.value = [1.3, 4.3, "6"]
            self.setting.adjust_value_to_type(source)
            self.assertEqual(self.setting.value, [1.3, 4.3, 6.0])

    def test_non_string_conffile(self):
        """with source conf file, trying to adjust a non-string with "conf-file" should fail"""
        self.setting.value = 1.0
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_string_conffile(self):
        """with source conf file, trying to adjust a string to float type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_float_conffile(self):
        """with source conf file, trying to adjust a float to float should convert to float"""
        self.setting.value = "2.1"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, 2.1)
    def test_adjust_int_conffile(self):
        """with source conf file, trying to adjust an int to float should convert to float"""
        self.setting.value = "2"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, 2.0)
        self.assert_(isinstance(self.setting.value, float))
    def test_adjust_bool_conffile(self):
        """with source conf file, trying to adjust a bool to float should fail"""
        self.setting.value = "true"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_list_conffile(self):
        """with source conf file, trying to adjust a list of int to float should convert """ \
            """to list of float"""
        self.setting.value = '(1, 4, 6)'
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [1.0, 4.0, 6.0])
    def test_adjust_list_float_conffile(self):
        """with source conf file, trying to adjust a list of float to float should convert """ \
            """to a list of float"""
        self.setting.value = "(1.2, 4.4, 6.3)"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [1.2, 4.4, 6.3])
    def test_adjust_list_mixed_conffile(self):
        """with source conf file, trying to adjust a list of mixed values to float should fail"""
        self.setting.value = '(1, 4, "6")'
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("conf file"))

    def test_non_string_keyval(self):
        """with source keyval list, trying to adjust a non-string with "keyval list" should fail"""
        self.setting.value = 1.0
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_string_keyval(self):
        """with source keyval list, trying to adjust a string to float type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_float_keyval(self):
        """with source keyval list, trying to adjust a float to float should convert to float"""
        self.setting.value = "2.1"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, 2.1)
        self.assert_(isinstance(self.setting.value, float))
    def test_adjust_int_keyval(self):
        """with source keyval list, trying to adjust an int to float should convert to float"""
        self.setting.value = "2"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, 2.0)
        self.assert_(isinstance(self.setting.value, float))
    def test_adjust_bool_keyval(self):
        """with source keyval list, trying to adjust a bool to float should fail"""
        self.setting.value = "true"
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_list_keyval(self):
        """with source keyval list, trying to convert lists should fail"""
        self.setting.value = '(1.0, 4.2, 6.1)'
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))

    def shortDescription(self):
        description = super(TestAdjustValueToTypeFloat, self).shortDescription()
        return "settings.Setting.adjust_value_to_type: " + (description or "")
    
class TestAdjustValueToTypeBool(unittest.TestCase):
    def setUp(self):
        self.setting = settings.Setting("key", True)
    def test_adjust_string_direct_default(self):
        """with source direct/default, trying to adjust a string to bool type should fail"""
        for source in ("direct", "default"):
            self.setting.value = u"hello"
            self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type(source))
    def test_adjust_float_direct_default(self):
        """with source direct/default, trying to adjust a float to bool should fail"""
        for source in ("direct", "default"):
            self.setting.value = 2.1
            self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type(source))
    def test_adjust_int_direct_default(self):
        """with source direct/default, trying to adjust an int to bool should fail"""
        for source in ("direct", "default"):
            self.setting.value = 2
            self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type(source))
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
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_string_conffile(self):
        """with source conf file, trying to adjust a string to bool type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_float_conffile(self):
        """with source conf file, trying to adjust a float to bool should fail"""
        self.setting.value = "2.1"
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_int_conffile(self):
        """with source conf file, trying to adjust an int to bool should fail"""
        self.setting.value = "2"
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_bool_conffile(self):
        """with source conf file, trying to adjust a bool to bool should convert to bool"""
        self.setting.value = "false"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, False)
    def test_adjust_list_conffile(self):
        """with source conf file, trying to adjust a list of int to bool should fail"""
        self.setting.value = '(1, 0, 6)'
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
# The following is a spurious test, see above
    def test_adjust_list_float_conffile(self):
        """with source conf file, trying to adjust a list of float to bool should convert """ \
            """to a list of bool"""
        self.setting.value = "(1.2, 4.4, 6.3)"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [True, True, True])
    def test_adjust_list_float_conffile(self):
        """with source conf file, trying to adjust a list of bool to bool should convert """ \
            """to a list of bool"""
        self.setting.value = '(yes, yes, no)'
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, [True, True, False])
    def test_adjust_list_mixed_conffile(self):
        """with source conf file, trying to adjust a list of mixed values to bool should fail"""
        self.setting.value = '(1, 4, "6")'
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))

    def test_non_string_keyval(self):
        """with source keyval list, trying to adjust a non-string with "keyval list" should fail"""
        self.setting.value = False
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_string_keyval(self):
        """with source keyval list, trying to adjust a string to bool type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_float_keyval(self):
        """with source keyval list, trying to adjust a float to bool should fail"""
        self.setting.value = "2.1"
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_int_keyval(self):
        """with source keyval list, trying to adjust an int to bool should convert to bool"""
        self.setting.value = "2"
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_bool_keyval(self):
        """with source keyval list, trying to adjust a bool to bool should convert to bool"""
        self.setting.value = "no"
        self.setting.adjust_value_to_type("keyval list")
        self.assertEqual(self.setting.value, False)
    def test_adjust_list_keyval(self):
        """with source keyval list, trying to convert lists should fail"""
        self.setting.value = '(1.0, 4.2, 6.1)'
        self.assertRaises(ValueError, lambda: self.setting.adjust_value_to_type("keyval list"))

    def shortDescription(self):
        description = super(TestAdjustValueToTypeBool, self).shortDescription()
        return "settings.Setting.adjust_value_to_type: " + (description or "")
    
for test_class in (TestGetBoolean, TestDetectType, TestAdjustValueToTypeInt,
                   TestAdjustValueToTypeFloat, TestAdjustValueToTypeBool):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))

suite.addTest(doctest.DocFileSuite("settings.txt"))
