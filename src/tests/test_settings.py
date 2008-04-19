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
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
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
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
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
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
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
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
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
        self.setting.value = u"2.1"
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_int_conffile(self):
        """with source conf file, trying to adjust an int to bool should fail"""
        self.setting.value = u"2"
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
    def test_adjust_bool_conffile(self):
        """with source conf file, trying to adjust a bool to bool should convert to bool"""
        self.setting.value = u"false"
        self.setting.adjust_value_to_type("conf file")
        self.assertEqual(self.setting.value, False)
    def test_adjust_list_conffile(self):
        """with source conf file, trying to adjust a list of int to bool should fail"""
        self.setting.value = u'(1, 0, 6)'
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))
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
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("conf file"))

    def test_non_string_keyval(self):
        """with source keyval list, trying to adjust a non-string should fail"""
        self.setting.value = False
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_string_keyval(self):
        """with source keyval list, trying to adjust a string to bool type should fail"""
        self.setting.value = u"hello"
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_float_keyval(self):
        """with source keyval list, trying to adjust a float to bool should fail"""
        self.setting.value = u"2.1"
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
    def test_adjust_int_keyval(self):
        """with source keyval list, trying to adjust an int to bool should convert to bool"""
        self.setting.value = u"2"
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("keyval list"))
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
        self.assertRaises(BaseException, lambda: self.setting.adjust_value_to_type("foobar"))
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
        :type source: str
        :type desired_value: float, unicode, bool, int, or list
        """
        setting.set_value(value, source)
        self.assertEqual(setting.value, desired_value if desired_value is not None else value)
        self.assert_(isinstance(setting.value, type_))

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
        """setting ony other but a string vis source="conf file"/"keyval list" should fail"""
        for source in ["conf file", "keyval list"]:
            self.assertRaises(BaseException, lambda: self.int_setting.set_value(1, source))
            self.assertRaises(BaseException, lambda: self.int_setting.set_value(1.3, source))
            self.assertRaises(BaseException, lambda: self.int_setting.set_value(True, source))
            self.assertRaises(BaseException,
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
        if self.list_setting:
            self.assume_working_value_setting(self.list_setting, u"3", unicode, u"(2, 3, -4)")
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

for test_class in (TestGetBoolean, TestDetectType, TestAdjustValueToTypeInt,
                   TestAdjustValueToTypeFloat, TestAdjustValueToTypeBool,
                   TestAdjustValueToTypeUnicode, TestAdjustValueToTypeInvalidSource,
                   TestSetValueDefaultFirst,
                   TestSetValueDefaultSecondDirect,
                   TestSetValueDefaultSecondConf,
                   TestSetValueDefaultSecondKeyval,
                   TestSetValueMisc):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))

suite.addTest(doctest.DocFileSuite("settings.txt"))
