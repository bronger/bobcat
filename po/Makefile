.PHONY: update

all: de.gmo

%.gmo : %.po
	find ../src -name "*.py" | xargs xgettext --output=bobcat.pot
	msgmerge --update $< bobcat.pot
	msgfmt --output-file=$@ $<
	mkdir -p `basename $@ .gmo`
	cp $@ `basename $@ .gmo`/bobcat.mo
