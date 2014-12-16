mkdir -p /usr/lib/tazpkg
# /usr/lib/slitaz ?

for i in \
	tazpkg tazpkg-box tazpkg-notify \
	modules/tazpkg-convert modules/tazpkg-find-depends \
	tazpanel/pkgs.cgi tazpanel/pkgs ;
do
	fi=$(basename $i)
	case $i in
		tazpanel/pkgs.cgi) DIR=/var/www/tazpanel ;;
		tazpanel/pkgs)	DIR=/var/www/tazpanel/menu.d ;;
		modules/*)	DIR=/usr/lib/tazpkg ;;
		*) DIR=/usr/bin ;;
	esac
	[ -f "$DIR/$fi" ] && rm $DIR/$fi
	wget -P $DIR hg.slitaz.org/tazpkg/raw-file/tip/$i
	chmod +x $DIR/$fi
done
