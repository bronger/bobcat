.PHONY: src-doc-sf src-doc doctests pylint src-doc-svn

src-doc-sf:
	rsync --rsh=ssh -avuz homepage/ shell.sourceforge.net:/home/groups/l/la/latex-bronger/htdocs/gummi/

src-doc:
	epydoc --config=misc/epydoc.cfg

src-doc-svn:
	svn co https://svn.origo.ethz.ch/bobcat/src-doc
	cp --recursive homepage/epydoc/* src-doc/
	svn propset svn:mime-type "image/png" src-doc/*.png
	svn propset svn:mime-type "image/gif" src-doc/*.gif
	svn propset svn:mime-type "text/css" src-doc/*.css
	svn propset svn:mime-type "text/html" src-doc/*.html
	svn propset svn:mime-type "text/javascript" src-doc/*.js
	svn add src-doc/*
	svn commit -m "Updated web sources documentation." src-doc/*
	rm -Rf src-doc

doctests:
	cd src; python common.py
	cd src; python settings.py
	cd src; python parser.py
	cd src; python helpers.py
	cd src; python i18n.py
	cd src; python latex_substitutions.py
	cd src; python preprocessor.py
	cd src; python safefilename.py

pylint:
	cd src; pylint --rcfile=../misc/pylint.cfg *.py > pylint.log
