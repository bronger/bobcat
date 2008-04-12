#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright © 2007, 2008 Torsten Bronger <bronger@physik.rwth-aachen.de>
#
#    This file is part of the Bobcat program.
#
#    Bobcat is free software; you can redistribute it and/or modify it under
#    the terms of the MIT licence:
#
#    Permission is hereby granted, free of charge, to any person obtaining a
#    copy of this software and associated documentation files (the "Software"),
#    to deal in the Software without restriction, including without limitation
#    the rights to use, copy, modify, merge, publish, distribute, sublicense,
#    and/or sell copies of the Software, and to permit persons to whom the
#    Software is furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in
#    all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#

u"""Internationalisation, aka i18n.

Part I: Translations of text snippets into various languages
============================================================

While is is quite easily possible to translate textual output of the program
into the language of the computer Bobcat is running on, Bobcat needs more than
this: It must generate translations into *arbitrary* languages, for example for
a German text processed on a French computer.  This is realised in this module,
for example:

    >>> gettext._default_localedir = "locale"
    >>> # The above line is not necessary in the final program of course.
    >>> translate(u"January", "de")
    u'Januar'
    >>> translate(u"January", "de-at")
    u'J\\xe4nner'

By the way, optionally this module doesn't translate strings if the *exact*
language is not available as an ``.mo`` file.  The rationale behind this is
that if sometime in the future, translations for this sub-language are added to
Bobcat, old documents that rely on the fallback may easily break.  In other
words, this strategy assumes that it is much more probably to have no
translations at all for a sub-language than to have incomplete ones:

    >>> translate(u"January", "de-de", strict=True)
    u'January'
    >>> translate(u"January", "de-de")
    u'Januar'

It's still possible – and very likely – that sub-language ``.mo`` files will
only provide a subset of translations and will pass the rest of the translation
requests to the parental ``.mo`` file:

    >>> translate(u"kiss", "de-de-1901")
    u'Ku\\xdf'
    >>> translate(u"January", "de-de-1901")
    u'Januar'

The ``.mo`` file may even be empty to state that this sub-language was also
looked at by a translator but, well, nothing differs from the parental
language:

    >>> translate(u"January", "de-ch", strict=True)
    u'Januar'

:var translations: translation container for the root domain of Bobcat for
  unstrict translations (see `Translations.__init__`).  A typical use of it
  is::

      translated_snippet = i18n.translations.translate(US_english_snippet,
                                                       language)

  Actually, this way via an instance of `Translations` like the above
  `translations` is only necessary if you need translations for another
  subdomain than the root domain.  For the root domain, there is a shortcut
  function `translate`, so that you can write::

      translated_snippet = i18n.translate(US_english_snippet, language)

:var translations_strict: like `translations`, however, this time the
  ``strict`` attribute is ``True`` for all values in this dictionary.

:var _translations: cached translations with no fallbacks set; only used in
  `translation`

:type translations: `Translations`
:type translations_strict: `Translations`
:type _translations: dict of ``gettext.GNUTranslations``


Part II: Language localisation aka l10n
=======================================

This is pretty straigtforward: the function `ugettext` is provided which does
the translation to the user's preferred language (well, hopefully).  Normally,
other modules will use this with::

    import i18n
    _ = i18n.ugettext

:var ugettext: contains the ``ugettext`` function for translation Unicode
  strings to the main language of the local machine.

:type ugettext: instancemethod
"""

# FixMe: Possibly it is better to do the fall-back to English (rather than the
# languages in-between) on a per-word basis rather than the per-language basis
# in "strict" mode.  I don't yet know, however, whether this is feasible with
# the gettext architecture.

import gettext, locale, copy, os.path, sys
from . import common

locale.setlocale(locale.LC_ALL, '')
if os.name == 'nt':
    # For Windows: set, if needed, a value in LANG environmental variable
    lang = os.getenv('LANG')
    if lang is None:
        lang = locale.getdefaultlocale()[0]  # en_US, fr_FR, el_GR etc..
    if lang:
        os.environ['LANG'] = lang
    del lang
preferred_encoding = locale.getpreferredencoding()
locale.setlocale(locale.LC_ALL, 'C')

if os.name == 'nt':
    ugettext = gettext.translation('bobcat', common.modulepath + "/po", fallback=True).ugettext
else:
    ugettext = gettext.translation('bobcat', fallback=True).ugettext
if 'epydoc' in sys.modules:
    ugettext = lambda s: s

def find(domain, language, strict):
    """Locate ``.mo`` files for the given language.  This function is a heavily
    modified version of the gettext function of the same name.

    :Parameters:
      - `domain`: gettext domain
      - `language`: language for which the ``.mo`` files should be located, in
        all-lowercase :RFC:`4646` form
      - `strict`: see `Translations.__init__`

    :type domain: str
    :type language: str
    :type strict: bool

    :Return:
      list of all file paths to the language ``.mo`` files.  Normally, this
      list has exactly one item, however, if `language` was a sub-language, it
      contains the fallbacks, too.

    :rtype: list
    """
    # Get some reasonable defaults for arguments that were not supplied
    localedir = gettext._default_localedir
    parts = language.split("-")
    posix_languages = [parts[0]]
    if len(parts) > 1:
        posix_languages.insert(0, posix_languages[0] + "_" + parts[1].upper())
    if len(parts) > 2:
        posix_languages.insert(0, posix_languages[0] + "@" + parts[2])
    # select a language
    result = []
    for i, posix_language in enumerate(posix_languages):
        mofile = os.path.join(localedir, posix_language, 'LC_MESSAGES', '%s.mo' % domain)
        if os.path.exists(mofile):
            result.append(mofile)
        elif strict and i == 0:
            return []
    return result

_translations = {}
def translation(domain, language, strict):
    """Get a ``gettext.GNUTranslations`` class instance for `language`, and in case
    `language` is a sub-language install proper fallbacks for missing
    translations.  This function is a heavily modified version of the gettext
    function of the same name.

    :Parameters:
      - `domain`: gettext domain
      - `language`: language for which translations should be looked for, in
        all-lowercase :RFC:`4646` form
      - `strict`: see `find`.

    :type domain: str
    :type language: str
    :type strict: bool

    :Return:
      the translations as a ``gettext.GNUTranslations`` object with proper
      fallbacks, or ``gettext.NullTranslations`` if no translations could be
      found

    :rtype: gettext.GNUTranslations
    """
    # pylint: disable-msg=C0103
    mofiles = find(domain, language, strict)
    if not mofiles:
        return gettext.NullTranslations()
    result = None
    for mofile in mofiles:
        key = os.path.abspath(mofile)
        t = _translations.get(key)
        if t is None:
            t = _translations.setdefault(key, gettext.GNUTranslations(open(mofile, 'rb')))
        # FixMe: The following Pylint directive is necessary because otherwise,
        # "result" is supposed to be None, which doesn't have an "add_fallback"
        # method.  Maybe Pylint (or rather astng) learns this someday.
        #
        # pylint: disable-msg=E1101
        #
        # Copy the translation object to allow setting fallbacks and
        # output charset. All other instance data is shared with the
        # cached object.
        t = copy.copy(t)
        if result is None:
            result = t
        else:
            result.add_fallback(t)
    return result

class Translations(object):
    """Class for translations for all languages but only one subdomain.

    This class is syntactic sugar and some sort of cache for translations with
    the GNU gettext tool.  Additionally, it maps :RFC:`4646` language codes to
    those used by gettext.

        >>> rtf_translations = Translations("rtf")
        >>> rtf_translations.translate("Highway", "de")
        u'Autobahn'

    :ivar domain: gettext domain for the translations provided by this class.
    :ivar all_gettext_translations: all so-far cached
      ``gettext.GNUTranslations`` instances for one language each

    :type domain: str
    :type all_gettext_translations: dict
    """
    def __init__(self, subdomain=None, strict=False):
        """
        :Parameters:
          - `subdomain`: the domain of all Bobcat translations must start with
            "bobcat".  However, third-party backends will want to have their
            own translation (``.mo``) files.  Therefore, they can define their
            own subdomain.  For example, the subdomain "mybackend" yields the
            domain name "bobcat_mybackend".  If `None`, the resulting domain is
            the main domain "bobcat".
          - `strict`: Only important if the target language is a sub-language,
            for example ``de-at``, while only for ``de`` the ``.mo`` file is
            available but not for ``de-at``.  In this case, ``strict=True``
            means that ``text`` is returned untranslated.  If ``False``, at
            least the ``de`` translation is returned.  Typically, ``True`` is
            used for matching parsed content, and ``False`` is used for
            generating translated content.

        :type subdomain: str
        :type strict: bool
        """
        if not subdomain:
            self.domain = "bobcat"
        else:
            self.domain = "bobcat_" + subdomain
        self.all_gettext_translations = {}
        self.strict = strict
    def translate(self, text, language):
        """Translate ``text`` to ``language``.  If language is ``None``, return
        ``text``.  (This special case is used by the parser before the very
        first child in the root document node has been created.  In this phase,
        the current document language is ``None``.)

        :Parameters:
          - `text`: US English text snipped that is to be translated
          - `language`: all-lowercase :RFC:`4646` language code of the target
            language

        :type text: unicode
        :type language: str
        
        :Return:
          The translation of ``text`` into ``language``

        :rtype: unicode
        """
        if language is None:
            return text
        gettext_translations = self.all_gettext_translations.get(language)
        if not gettext_translations:
            gettext_translations = translation(self.domain, language, self.strict)
            self.all_gettext_translations[language] = gettext_translations
        return gettext_translations.ugettext(text)
            
translations = Translations()
translations_strict = Translations(strict=True)
def translate(text, language, strict=False):
    """Translate ``text`` to ``language``, using the translations in Bobcat's
    root gettext domain.  If you want to have an own domain for your
    third-party contribution, make your own instance of `Translations` and use
    its `Translations.translate` method.

    :Parameters:
      - `text`: US English text snipped that is to be translated
      - `language`: all-lowercase :RFC:`4646` language code of the target
        language
      - `strict`: see `Translations.__init__`

    :type text: unicode
    :type language: str
    :type strict: bool
    
    :Return:
      The translation of ``text`` into ``language``

    :rtype: unicode
    """
    if strict:
        return translations_strict.translate(text, language)
    else:
        return translations.translate(text, language)


def match_language_dependently(match_string, excerpt, pos, language, unescaped_only=True):
    """Test whether a string, or its translation into the current document
    language, matches a certain part of the input script.

        >>> filename = "test2.bcat"
        >>> open(filename, "w").write(\""".. -*- coding: utf-8 -*-
        ... .. Bobcat 1.0
        ...
        ... Januar
        ... \\January
        ... \""")
        >>> import preprocessor
        >>> text, __, __ = preprocessor.load_file(filename)
        >>> os.remove(filename)
        >>> match_language_dependently(u"January", text, 3, "de")
        True
        >>> match_language_dependently(u"January", text, 10, "de", unescaped_only=False)
        True
        >>> match_language_dependently(u"January", text, 10, "de")
        False
        >>> match_language_dependently(u"January", text, 3, "de-de")  # no .mo for de-de
        False

    :Parameters:
      - `match_string`: the string to test for, in US English
      - `excerpt`: the Bobcat excerpt in which the match should be tested
      - `pos`: starting position of the match
      - `language`: :RFC:`4646` code for the current document language
      - `unescaped_only`: if ``True``, match only of all matched characters
        were not escaped.  This is necessary for built-in directives.  For
        (syntactically similar) *environments*, however, it is not necessary
        for the name to be escaped, in order to have names that are built-ins
        at the same time.  Thus, the parser will first test for built-ins, and
        then for user-provided environments.

    :Return:
      ``True`` if there was a match, ``False`` otherwise

    :rtype: bool
    """
    if unescaped_only:
        text = excerpt.escaped_text()
    else:
        text = unicode(excerpt)
    return text.startswith(match_string, pos) or \
        text.startswith(translate(match_string, language, strict=True), pos)
