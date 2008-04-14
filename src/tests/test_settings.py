#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, doctest
from bobcatlib import settings

suite = unittest.TestSuite()

suite.addTest(doctest.DocTestSuite("bobcatlib.settings"))
suite.addTest(doctest.DocFileSuite("settings.txt"))
