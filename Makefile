# Makefile for Tazpkg.
#
PREFIX?=/usr
DOCDIR?=$(PREFIX)/share/doc
LIBDIR?=$(PREFIX)/lib/slitaz
SYSCONFDIR?=/etc/slitaz
DESTDIR?=
LINGUAS?=fr

VERSION:=$(shell grep ^VERSION=[0-9] tazpkg | cut -d '=' -f 2)

all:
	
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
		echo -n "Updating $$l po file."; \
		msgmerge -U po/tazpkg/$$l.po po/tazpkg/tazpkg.pot ; \
	done;

msgfmt:
	@for l in $(LINGUAS); do \
		echo "Compiling $$l mo file..."; \
		mkdir -p po/mo/$$l/LC_MESSAGES; \
		msgfmt -o po/mo/$$l/LC_MESSAGES/tazpkg.mo po/tazpkg/$$l.po ; \
	done;

# Installation.

install: msgfmt
	# Tazpkg command line interface
	install -m 0755 -d $(DESTDIR)$(PREFIX)/bin
	install -m 0777 tazpkg $(DESTDIR)$(PREFIX)/bin
	# Tazpkgbox GUI
	install -m 0777 tazpkgbox $(DESTDIR)$(PREFIX)/bin
	install -m 0777 tazpkgbox-install $(DESTDIR)$(PREFIX)/bin
	install -m 0755 -d $(DESTDIR)$(LIBDIR)
	install -m 0777 lib/libtazpkgbox $(DESTDIR)$(LIBDIR)
	# Configuration files
	install -m 0755 -d $(DESTDIR)$(SYSCONFDIR)
	install -m 0644 tazpkg.conf $(DESTDIR)$(SYSCONFDIR)
	# Documentation
	install -m 0755 -d $(DESTDIR)$(DOCDIR)/tazpkg
	cp -a doc/* $(DESTDIR)$(DOCDIR)/tazpkg
	# The i18n files
	mkdir -p $(DESTDIR)$(PREFIX)/share/locale
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
	rm -rf $(DESTDIR)$(LIBDIR)/tazpkgbox
	rm -f $(DESTDIR)$(LIBDIR)/libtazpkgbox
	rm -rf $(DESTDIR)$(DOCDIR)/tazpkg
	rm -f $(DESTDIR)$(SYSCONFDIR)/tazpkg.conf 
	rm -rf $(DESTDIR)$(PREFIX)/share/locale/*/LC_MESSAGES/tazpkg*.mo

clean:
	rm -rf _pkg
	rm -rf po/mo
	rm -f po/*/*~
	
