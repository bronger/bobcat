.PHONY: src-doc-sf src-doc tests pylint src-doc-svn

src-doc-sf:
	rsync --rsh=ssh -avuz homepage/ shell.sourceforge.net:/home/groups/l/la/latex-bronger/htdocs/gummi/

src-doc:
	cd src ; epydoc --config=../misc/epydoc.cfg

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

tests:
	python src/tests/test_doctests.py

pylint:
	cd src/gummi; pylint --rcfile=../misc/pylint.cfg *.py > pylint.log
