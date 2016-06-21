#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append("/home/bronger/src/bobcat/maths/src")
from bobcatlib.parser import maths
from bobcatlib import preprocessor, helpers, parser

text = preprocessor.Excerpt("{a = b}", "PRE", "test.bcat", {}, {})

document = parser.Document()
document.parse(text)
helpers.visualize_tree(document.tree_list(), "bobcat.eps")
