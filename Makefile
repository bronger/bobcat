.PHONY: homepage websources doctests

homepage:
	rsync --rsh=ssh -avuz homepage/ shell.sourceforge.net:/home/groups/l/la/latex-bronger/htdocs/gummi/

websources:
	epydoc --config=misc/epydoc.cfg

doctests:
	cd src; python common.py
	cd src; python helpers.py
	cd src; python i18n.py
	cd src; python latex_substitutions.py
	cd src; python preprocessor.py
	cd src; python safefilename.py
