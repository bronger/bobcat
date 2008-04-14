#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from tests import common_test

suite = unittest.TestSuite()

from tests import test_common, test_helpers, test_preprocessor, test_settings, test_safefilename, \
    test_i18n, test_emitter, test_latex_substitutions
suite.addTests([test_common.suite,
                test_helpers.suite,
                test_preprocessor.suite,
                test_settings.suite,
                test_safefilename.suite,
                test_i18n.suite,
                test_emitter.suite,
                test_latex_substitutions.suite])

common_test.chdir_to_testbed()
runner = unittest.TextTestRunner()
runner.run(suite)
