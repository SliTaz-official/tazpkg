# Makefile for TazPkg.
#
PREFIX?=/usr
DOCDIR?=$(PREFIX)/share/doc
SYSCONFDIR?=/etc/slitaz
DESTDIR?=
LINGUAS?=el es fr pl pt_BR ru sv

VERSION:=$(shell grep ^VERSION=[0-9] tazpkg | cut -d '=' -f 2)

tmpdir = tar-install/tazpkg-$(VERSION)
tarball = tazpkg-$(VERSION).tar.gz

all: msgfmt

# i18n.

pot:
	xgettext -o po/tazpkg.pot -L Shell \
		--package-name=TazPkg \
		--package-version="$(VERSION)" -kaction -ktitle \
		./tazpkg ./tazpkg-box ./pkgs ./pkgs.cgi ./tazpkg-notify

msgmerge:
	@for l in $(LINGUAS); do \
		if [ -f "po/$$l.po" ]; then \
			echo -n "Updating $$l po file."; \
			msgmerge -U po/$$l.po po/tazpkg.pot ; \
		fi; \
	done

msgfmt:
	@for l in $(LINGUAS); do \
		if [ -f "po/$$l.po" ]; then \
			echo -n "Compiling tazpkg $$l mo file... "; \
			mkdir -p po/mo/$$l/LC_MESSAGES; \
			msgfmt -o po/mo/$$l/LC_MESSAGES/tazpkg.mo \
				po/$$l.po ; \
			echo "done"; \
		fi; \
	done;

# Installation.

install: msgfmt
	# TazPkg command line interface
	install -m 0755 -d $(DESTDIR)$(PREFIX)/bin
	install -m 0777 tazpkg $(DESTDIR)$(PREFIX)/bin
	# TazPkg-box GUI
	install -m 0777 tazpkg-notify $(DESTDIR)$(PREFIX)/bin
	install -m 0777 tazpkg-box $(DESTDIR)$(PREFIX)/bin
	# Configuration files
	install -m 0755 -d $(DESTDIR)$(SYSCONFDIR)
	install -m 0644 tazpkg.conf $(DESTDIR)$(SYSCONFDIR)
	# Documentation
	install -m 0755 -d $(DESTDIR)$(DOCDIR)/tazpkg
	cp -a doc/* $(DESTDIR)$(DOCDIR)/tazpkg
	# TazPanel files
	install -m 0755 -d $(DESTDIR)/var/www/tazpanel/menu.d
	cp -a pkgs.cgi $(DESTDIR)/var/www/tazpanel
	cp -a pkgs $(DESTDIR)/var/www/tazpanel/menu.d
	# The i18n files
	install -m 0755 -d $(DESTDIR)$(PREFIX)/share/locale
	cp -a po/mo/* $(DESTDIR)$(PREFIX)/share/locale
	# Desktop integration
	mkdir -p $(DESTDIR)$(PREFIX)/share
	cp -a  applications $(DESTDIR)$(PREFIX)/share
	cp -a  mime $(DESTDIR)$(PREFIX)/share
	cp -a  pixmaps $(DESTDIR)$(PREFIX)/share
	# TazPKG Notify XDG autostart
	mkdir -p $(DESTDIR)/etc/xdg
	cp -a xdg/autostart $(DESTDIR)/etc/xdg
	

# Uninstallation and clean-up commands.

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/tazpkg
	rm -f $(DESTDIR)$(PREFIX)/bin/tazpkg-box
	rm -f $(DESTDIR)$(PREFIX)/var/www/tazpanel/menu.d/pkgs
	rm -f $(DESTDIR)$(PREFIX)/var/www/tazpanel/pkgs.cgi
	rm -rf $(DESTDIR)$(PREFIX)/tazpkg-notify
	rm -rf $(DESTDIR)$(DOCDIR)/tazpkg
	rm -f $(DESTDIR)$(SYSCONFDIR)/tazpkg.conf 
	rm -rf $(DESTDIR)$(PREFIX)/share/locale/*/LC_MESSAGES/tazpkg*.mo

clean:
	rm -rf _pkg
	rm -rf tar-install
	rm -rf po/mo
	rm -f po/*~
	rm -f po/*.mo
	

targz:
	rm -rf ${tmpdir}
	mkdir -p ${tmpdir}
	
	make DESTDIR=${tmpdir} install
	
	cd tar-install ; \
	tar cvzf ${tarball} tazpkg-$(VERSION) ; \
	cd -
	
	@echo "** Tarball successfully created in tar-install/${tarball}"

help:
	@echo "make [ pot | msgmerge | msgfmt | all | install | uninstall | clear | targz ]"
