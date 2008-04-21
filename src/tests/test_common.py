#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, doctest
from bobcatlib import common

suite = unittest.TestSuite()

class TestParseLocalVariables(unittest.TestCase):
    def shortDescription(self):
        description = super(TestParseLocalVariables, self).shortDescription()
        return "common.parse_local_variables: " + (description or "")

for test_class in (TestParseLocalVariables,):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))

suite.addTest(doctest.DocFileSuite("common.txt"))
