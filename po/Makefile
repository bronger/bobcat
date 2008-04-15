.PHONY: update

all: de.gmo fr.gmo

%.gmo : %.po
	cd ../src ; xgettext --output=../po/bobcat.pot bobcat.py bobcat_rating.py
	msgmerge --update $< bobcat.pot
	msgfmt --output-file=$@ $<
	mkdir -p `basename $@ .gmo`
	cp $@ `basename $@ .gmo`/bobcat.mo
