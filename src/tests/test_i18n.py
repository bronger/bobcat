#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, doctest
from bobcatlib import i18n

suite = unittest.TestSuite()

suite.addTest(doctest.DocTestSuite("bobcatlib.i18n"))

