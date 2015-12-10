# Makefile for TazPkg.
#
prefix      ?= /usr
exec_prefix ?= $(prefix)
bindir      ?= $(exec_prefix)/bin
libexecdir  ?= $(exec_prefix)/libexec
datarootdir ?= $(prefix)/share
sysconfdir  ?= /etc
docdir      ?= $(datarootdir)/doc/tazpkg
libdir      ?= $(exec_prefix)/lib
localedir   ?= $(datarootdir)/locale
iconsdir    ?= $(datarootdir)/icons

DESTDIR ?=
LINGUAS ?= el es fr pl pt_BR ru sv zh_CN zh_TW
MODULES := $(shell ls modules)

VERSION := 5.0
ICONS = $(DESTDIR)$(iconsdir)/hicolor/32x32

tmpdir = tar-install/tazpkg-$(VERSION)
tarball = tazpkg-$(VERSION).tar.gz

.PHONY: all pot msgmerge msgfmt install uninstall clean targz help

all: msgfmt
	mkdir build
	cp -a tazpkg tazpkg-box tazpkg-notify \
		modules/* tazpanel/pkgs.cgi tazpanel/pkgs.css \
		doc/tazpkg.*.html build
	./stripall.sh

	# Substitute "@@MODULES@@" with modules path
	find build -type f -exec sed -i "s|@@MODULES@@|$(libexecdir)/tazpkg|g" \{\} \;

# i18n.

pot:
	xgettext -o po/tazpkg.pot -L Shell \
		--package-name=TazPkg \
		--package-version="$(VERSION)" -kaction -ktitle -kdie -k_ -k_n -k_p:1,2 \
		tazpkg \
		$(foreach module, $(MODULES), modules/$(module) ) \
		tazpkg-box tazpkg-notify tazpanel/pkgs.cgi

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
	install -m 0755 -d           $(DESTDIR)$(bindir)
	install -m 0755 build/tazpkg $(DESTDIR)$(bindir)

	# TazPkg modules
	install -m 0755 -d                $(DESTDIR)$(libexecdir)/tazpkg
	$(foreach module, $(MODULES), install -m 0755 build/$(module) $(DESTDIR)$(libexecdir)/tazpkg;)

	# TazPkg-box GUI
	install -m 0777 build/tazpkg-notify $(DESTDIR)$(bindir)
	install -m 0777 build/tazpkg-box    $(DESTDIR)$(bindir)

	# Configuration files
	install -m 0755 -d          $(DESTDIR)$(sysconfdir)/slitaz
	install -m 0644 tazpkg.conf $(DESTDIR)$(sysconfdir)/slitaz
	sed -i "s|@@sysconfdir@@|$(sysconfdir)|g" $(DESTDIR)$(sysconfdir)/slitaz/tazpkg.conf

	# Documentation
	install -m 0755 -d $(DESTDIR)$(docdir)
	cp -a build/tazpkg.*.html $(DESTDIR)$(docdir)
	ln -sf tazpkg.en.html $(DESTDIR)$(docdir)/tazpkg.html

	# TazPanel files
	install -m 0755 -d             $(DESTDIR)/var/www/tazpanel/menu.d
	install -m 0755 build/pkgs.cgi $(DESTDIR)/var/www/tazpanel
	ln -fs ../pkgs.cgi             $(DESTDIR)/var/www/tazpanel/menu.d/pkgs
	install -m 0755 -d             $(DESTDIR)/var/www/tazpanel/styles/default
	install -m 0644 build/gz/pkgs.css.gz $(DESTDIR)/var/www/tazpanel/styles/default

	# The i18n files
	install -m 0755 -d $(DESTDIR)$(localedir)
	cp -a po/mo/*      $(DESTDIR)$(localedir)

	# Desktop integration
	install -m 0755 -d                     $(DESTDIR)$(datarootdir)/applications
	install -m 0644 applications/*.desktop $(DESTDIR)$(datarootdir)/applications
	#cp -a mime         $(DESTDIR)$(datarootdir) # moved to shared-mime-info package

	# Default icons
	install -m 0755 -d $(ICONS)/apps
	install -m 0755 -d $(ICONS)/actions
	install -m 0755 -d $(ICONS)/status
	install -m 0644    pixmaps/tazpkg.png           $(ICONS)/apps
	install -m 0644    pixmaps/tazpkg-up.png        $(ICONS)/actions
	install -m 0644    pixmaps/tazpkg-installed.png $(ICONS)/status
	#ln -fs tazpkg.png  $(ICONS)/apps/TazPkg.png     # icon for Yad

	# TazPkg Notify XDG autostart
	mkdir -p            $(DESTDIR)$(sysconfdir)/xdg
	cp -a xdg/autostart $(DESTDIR)$(sysconfdir)/xdg


# Uninstallation and clean-up commands.

uninstall:
	rm -f  $(DESTDIR)$(bindir)/tazpkg
	rm -rf $(DESTDIR)$(libexecdir)/tazpkg

	rm -f  $(DESTDIR)$(bindir)/tazpkg-notify
	rm -f  $(DESTDIR)$(bindir)/tazpkg-box

	rm -f  $(DESTDIR)$(sysconfdir)/slitaz/tazpkg.conf

	rm -rf $(DESTDIR)$(docdir)/tazpkg*.html
	rm     $(DESTDIR)$(docdir)

	rm -f  $(DESTDIR)/var/www/tazpanel/pkgs.cgi
	rm -f  $(DESTDIR)/var/www/tazpanel/menu.d/pkgs
	rm -f  $(DESTDIR)/var/www/tazpanel/styles/default/pkgs.css

	rm -rf $(DESTDIR)$(localedir)/*/LC_MESSAGES/tazpkg.mo

	rm -f  $(DESTDIR)$(datarootdir)/applications/tazpkg-*.desktop
	rm -f  $(DESTDIR)$(datarootdir)/applications/tazpanel-pkgs.desktop

	rm -f  $(ICONS)/apps/tazpkg.png
	rm -f  $(ICONS)/actions/tazpkg-up.png
	rm -f  $(ICONS)/status/tazpkg-installed.png

	rm -f  $(DESTDIR)$(sysconfdir)/xdg/autostart/tazpkg-notify.desktop


clean:
	rm -rf build
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
	tar -cvzf ${tarball} tazpkg-$(VERSION) ; \
	cd -

	@echo "** Tarball successfully created in tar-install/${tarball}"


help:
	@echo "make [ pot | msgmerge | msgfmt | all | install | uninstall | clear | targz ]"
