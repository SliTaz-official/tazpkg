# Makefile for Tazpkg.
#
PREFIX?=/usr
DOCDIR?=$(PREFIX)/share/doc
SYSCONFDIR?=/etc/slitaz
DESTDIR?=
LINGUAS?=fr pt

VERSION:=$(shell grep ^VERSION=[0-9] tazpkg | cut -d '=' -f 2)

all: msgfmt
	
# i18n.

pot:
	xgettext -o po/tazpkg/tazpkg.pot -L Shell \
		--package-name=Tazpkg \
		--package-version="$(VERSION)" ./tazpkg
	xgettext -o po/tazpkg-notify/tazpkg-notify.pot -L Shell \
		--package-name="Tazpkg Notification" \
		--package-version="$(VERSION)" ./tazpkg-notify
	
msgmerge:
	@for l in $(LINGUAS); do \
		if [ -f "po/tazpkg/$$l.po" ]; then \
			echo -n "Updating $$l po file."; \
			msgmerge -U po/tazpkg/$$l.po po/tazpkg/tazpkg.pot ; \
		fi; \
		if [ -f "po/tazpkg-notify/$$l.po" ]; then \
			echo -n "Updating $$l po file."; \
			msgmerge -U po/tazpkg-notify/$$l.po po/tazpkg-notify/tazpkg-notify.pot; \
		fi; \
	done

msgfmt:
	@for l in $(LINGUAS); do \
		if [ -f "po/tazpkg/$$l.po" ]; then \
			echo -n "Compiling tazpkg $$l mo file... "; \
			mkdir -p po/mo/$$l/LC_MESSAGES; \
			msgfmt -o po/mo/$$l/LC_MESSAGES/tazpkg.mo \
				po/tazpkg/$$l.po ; \
			echo "done"; \
		fi; \
		if [ -f "po/tazpkg-notify/$$l.po" ]; then \
			echo -n "Compiling tazpkg-notify $$l mo file... "; \
			mkdir -p po/mo/$$l/LC_MESSAGES; \
			msgfmt -o po/mo/$$l/LC_MESSAGES/tazpkg-notify.mo \
				po/tazpkg-notify/$$l.po ; \
			echo "done"; \
		fi; \
	done;

# Installation.

install:
	# Tazpkg command line interface
	install -m 0755 -d $(DESTDIR)$(PREFIX)/bin
	install -m 0777 tazpkg $(DESTDIR)$(PREFIX)/bin
	# Tazpkgbox GUI
	install -m 0777 tazpkg-notify $(DESTDIR)$(PREFIX)/bin
	install -m 0777 tazpkgbox-install $(DESTDIR)$(PREFIX)/bin
	# Configuration files
	install -m 0755 -d $(DESTDIR)$(SYSCONFDIR)
	install -m 0644 tazpkg.conf $(DESTDIR)$(SYSCONFDIR)
	# Documentation
	install -m 0755 -d $(DESTDIR)$(DOCDIR)/tazpkg
	cp -a doc/* $(DESTDIR)$(DOCDIR)/tazpkg
	# The i18n files
	cp -a po/mo/* $(DESTDIR)$(PREFIX)/share/locale
	# Desktop integration
	mkdir -p $(DESTDIR)$(PREFIX)/share
	cp -a  applications $(DESTDIR)$(PREFIX)/share
	cp -a  mime $(DESTDIR)$(PREFIX)/share
	cp -a  pixmaps $(DESTDIR)$(PREFIX)/share

# Uninstallation and clean-up commands.

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/tazpkg
	rm -f $(DESTDIR)$(PREFIX)/bin/tazpkgbox
	rm -rf $(DESTDIR)$(PREFIX)/tazpkg-notify
	rm -f $(DESTDIR)$(PREFIX)/tazpkgbox-install
	rm -rf $(DESTDIR)$(DOCDIR)/tazpkg
	rm -f $(DESTDIR)$(SYSCONFDIR)/tazpkg.conf 
	rm -rf $(DESTDIR)$(PREFIX)/share/locale/*/LC_MESSAGES/tazpkg*.mo

clean:
	rm -rf _pkg
	rm -rf po/mo
	rm -f po/*/*~
	rm -f po/*/*.mo
	
