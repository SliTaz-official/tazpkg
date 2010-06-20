# Makefile for Tazpkg.
#
PREFIX?=/usr
DOCDIR?=$(PREFIX)/share/doc
LIBDIR?=$(PREFIX)/lib/slitaz
SYSCONFDIR?=/etc/slitaz
DESTDIR?=
LINGUAS?=fr

all:
	
# i18n.

pot:
	xgettext -o po/tazpkg/tazpkg.pot -L Shell --package-name=Tazpkg ./tazpkg
	
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
	@echo "Installing Tazpkg..."
	install -g root -o root -m 0755 -d $(DESTDIR)$(PREFIX)/bin
	install -g root -o root -m 0777 tazpkg $(DESTDIR)$(PREFIX)/bin
	install -g root -o root -m 0777 tazpkgbox $(DESTDIR)$(PREFIX)/bin
	@echo "Installing Tazpkgbox libraries..."
	install -g root -o root -m 0755 -d $(DESTDIR)$(LIBDIR)
	cp -a lib/tazpkgbox $(DESTDIR)$(LIBDIR)
	@echo "Installing configuration files..."
	install -g root -o root -m 0755 -d $(DESTDIR)$(SYSCONFDIR)
	install -g root -o root -m 0644 tazpkg.conf $(DESTDIR)$(SYSCONFDIR)
	@echo "Installing documentation files..."
	install -g root -o root -m 0755 -d $(DESTDIR)$(DOCDIR)/tazpkg
	install -g root -o root -m 0644 doc/* $(DESTDIR)$(DOCDIR)/tazpkg
	# i18n
	mkdir -p $(DESTDIR)$(PREFIX)/share/locale
	cp -a po/mo/* $(DESTDIR)$(PREFIX)/share/locale
	# Desktop integration
	@echo "Setting up desktop integration..."
	mkdir -p $(DESTDIR)$(PREFIX)/share
	cp -a  applications $(DESTDIR)$(PREFIX)/share

# Uninstallation and clean-up commands.

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/tazpkg
	rm -f $(DESTDIR)$(PREFIX)/bin/tazpkgbox
	rm -rf $(DESTDIR)$(LIBDIR)/tazpkgbox
	rm -rf $(DESTDIR)$(DOCDIR)/tazpkg
	rm -f $(DESTDIR)$(SYSCONFDIR)/tazpkg.conf 
	rm -rf $(DESTDIR)$(PREFIX)/share/locale/*/LC_MESSAGES/tazpkg*.mo

clean:
	rm -rf _pkg
	rm -rf po/mo
	
