# Makefile for Tazpkg.
#
PREFIX?=/usr
DOCDIR?=$(PREFIX)/share/doc
LIBDIR?=$(PREFIX)/lib/slitaz
SYSCONFDIR?=/etc/slitaz

all:
	grep "^VERSION=[0-9]" tazpkg | sed 's/VERSION=//'
	
install:
	@echo "Installing Tazpkg into $(PREFIX)/bin..."
	install -g root -o root -m 0755 -d $(PREFIX)/bin
	install -g root -o root -m 0777 tazpkg $(PREFIX)/bin
	install -g root -o root -m 0777 tazpkgbox $(PREFIX)/bin
	@echo "Installing Tazpkgbox lib into $(LIBDIR)..."
	install -g root -o root -m 0755 -d $(LIBDIR)
	cp -a lib/tazpkgbox $(LIBDIR)
	@echo "Installing configuration files..."
	install -g root -o root -m 0755 -d $(SYSCONFDIR)
	install -g root -o root -m 0644 tazpkg.conf $(SYSCONFDIR)
	@echo "Installing documentation files..."
	install -g root -o root -m 0755 -d $(DOCDIR)/tazpkg
	install -g root -o root -m 0644 doc/* $(DOCDIR)/tazpkg

uninstall:
	rm -f $(PREFIX)/bin/tazpkg
	rm -f $(PREFIX)/bin/tazpkgbox
	rm -f $(LIBDIR)/tazpkgbox
	rm -rf $(DOCDIR)/tazpkg

