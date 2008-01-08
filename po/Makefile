.PHONY: update

all: de.gmo fr.gmo

%.gmo : %.po
	cd ../src ; xgettext --output=../po/gummi.pot gummi.py gummi_rating.py
	msgmerge --update $< gummi.pot
	msgfmt --output-file=$@ $<
	mkdir -p `basename $@ .gmo`
	cp $@ `basename $@ .gmo`/gummi.mo
