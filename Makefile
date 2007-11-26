# Makefile for Tazpkg.
#
PREFIX?=/usr
DOCDIR?=/usr/share/doc

all:
    
install:
	@echo "Installing Tazpkg into $(PREFIX)/bin..."
	install -g root -o root -m 0777 tazpkg $(PREFIX)/bin
	@echo "Installing documentation files..."
	install -g root -o root -m 0755 -d $(DOCDIR)/tazpkg
	install -g root -o root -m 0644 doc/* $(DOCDIR)/tazpkg

uninstall:
	rm -f $(PREFIX)/bin/tazpkg
	rm -rf $(DOCDIR)/tazpkg
