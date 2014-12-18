# Makefile for TazPkg.
#
PREFIX?=/usr
DOCDIR?=$(PREFIX)/share/doc
SYSCONFDIR?=/etc/slitaz
DESTDIR?=
LINGUAS?=el es fr pl pt_BR ru sv zh_CN zh_TW

VERSION:=$(shell grep ^VERSION=[0-9] tazpkg | cut -d '=' -f 2)
ICONS = $(DESTDIR)$(PREFIX)/share/icons/hicolor/32x32

tmpdir = tar-install/tazpkg-$(VERSION)
tarball = tazpkg-$(VERSION).tar.gz

all: msgfmt


# i18n.

pot:
	xgettext -o po/tazpkg.pot -L Shell \
		--package-name=TazPkg \
		--package-version="$(VERSION)" -kaction -ktitle -k_ -k_n -k_p:1,2 \
		./tazpkg ./tazpkg-convert ./tazpkg-find-depends ./tazpkg-box \
		./pkgs ./pkgs.cgi ./tazpkg-notify

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
	install -m 0755 -d                  $(DESTDIR)$(PREFIX)/bin
	install -m 0777 tazpkg              $(DESTDIR)$(PREFIX)/bin
	-[ "$(VERSION)" ] && sed -i 's/^VERSION=[0-9].*/VERSION=$(VERSION)/' $(DESTDIR)$(PREFIX)/bin/tazpkg
	install -m 0777 modules/tazpkg-convert      $(DESTDIR)$(PREFIX)/bin
	install -m 0755 -d                          $(DESTDIR)$(PREFIX)/lib/tazpkg
	install -m 0777 modules/tazpkg-find-depends $(DESTDIR)$(PREFIX)/lib/tazpkg

	# TazPkg-box GUI
	install -m 0777 tazpkg-notify $(DESTDIR)$(PREFIX)/bin
	install -m 0777 tazpkg-box    $(DESTDIR)$(PREFIX)/bin

	# Configuration files
	install -m 0755 -d          $(DESTDIR)$(SYSCONFDIR)
	install -m 0644 tazpkg.conf $(DESTDIR)$(SYSCONFDIR)

	# Documentation
	install -m 0755 -d $(DESTDIR)$(DOCDIR)/tazpkg
	cp -a doc/*        $(DESTDIR)$(DOCDIR)/tazpkg

	# TazPanel files
	install -m 0755 -d      $(DESTDIR)/var/www/tazpanel/menu.d
	cp -a tazpanel/pkgs.cgi $(DESTDIR)/var/www/tazpanel
	cp -a tazpanel/pkgs     $(DESTDIR)/var/www/tazpanel/menu.d
	install -m 0755 -d      $(DESTDIR)/var/www/tazpanel/styles/default
	cp -a tazpanel/pkgs.css $(DESTDIR)/var/www/tazpanel/styles/default

	# The i18n files
	install -m 0755 -d $(DESTDIR)$(PREFIX)/share/locale
	cp -a po/mo/*      $(DESTDIR)$(PREFIX)/share/locale

	# Desktop integration
	mkdir -p           $(DESTDIR)$(PREFIX)/share
	cp -a applications $(DESTDIR)$(PREFIX)/share
	#cp -a mime         $(DESTDIR)$(PREFIX)/share # moved to shared-mime-info package

	# Default icons
	install -m 0755 -d $(ICONS)/apps
	install -m 0644 pixmaps/tazpkg.png $(ICONS)/apps
	ln -fs tazpkg.png $(ICONS)/apps/TazPkg.png # icon for Yad
	install -m 0755 -d $(ICONS)/actions
	install -m 0644 pixmaps/tazpkg-up.png $(ICONS)/actions
	install -m 0755 -d $(ICONS)/status
	install -m 0644 pixmaps/tazpkg-installed.png $(ICONS)/status

	# TazPkg Notify XDG autostart
	mkdir -p            $(DESTDIR)/etc/xdg
	cp -a xdg/autostart $(DESTDIR)/etc/xdg


# Uninstallation and clean-up commands.

uninstall:
	rm -f  $(DESTDIR)$(PREFIX)/bin/tazpkg
	rm -f  $(DESTDIR)$(PREFIX)/bin/tazpkg-convert
	rm -f  $(DESTDIR)$(PREFIX)/lib/tazpkg/tazpkg-find-depends

	rm -f  $(DESTDIR)$(PREFIX)/bin/tazpkg-notify
	rm -f  $(DESTDIR)$(PREFIX)/bin/tazpkg-box

	rm -f  $(DESTDIR)$(SYSCONFDIR)/tazpkg.conf

	rm -rf $(DESTDIR)$(DOCDIR)/tazpkg

	rm -f  $(DESTDIR)/var/www/tazpanel/pkgs.cgi
	rm -f  $(DESTDIR)/var/www/tazpanel/menu.d/pkgs

	rm -rf $(DESTDIR)$(PREFIX)/share/locale/*/LC_MESSAGES/tazpkg.mo

	rm -f  $(DESTDIR)$(PREFIX)/share/applications/tazpkg-*.desktop
	rm -f  $(DESTDIR)$(PREFIX)/share/applications/tazpanel-pkgs.desktop

	rm -f  $(ICONS)/apps/tazpkg.png
	rm -f  $(ICONS)/actions/tazpkg-up.png
	rm -f  $(ICONS)/status/tazpkg-installed.png

	rm -f  $(DESTDIR)/etc/xdg/autostart/tazpkg-notify.desktop


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
