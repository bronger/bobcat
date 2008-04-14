#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest, doctest
from bobcatlib import common

suite = unittest.TestSuite()

suite.addTest(doctest.DocTestSuite("bobcatlib.common"))
suite.addTest(doctest.DocFileSuite("common.txt"))
