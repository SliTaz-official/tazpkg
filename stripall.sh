#!/bin/sh
# TazPkg - SliTaz Package Manager, hg.slitaz.org/tazpkg
# stripall.sh - strip and compact resources in build process
# Copyright (C) 2015 SliTaz GNU/Linux - BSD License


substitute_icons() {
	# Customize sed script
	cp "$sed_script" "$sed_script.do"
	sed -i "s|@@@|$1|" "$sed_script.do"
	# Run sed script
	sh "$sed_script.do"
	rm "$sed_script.do"
}


# Make script for substitution
	sed_script="$(mktemp)"
	echo -n "sed -i '" > "$sed_script"
	echo -e "\
	add				\n	admin			\n	back			\n	battery	
	brightness		\n	cancel			\n	cd				\n	check	
	clock			\n	conf			\n	daemons			\n	delete	
	detect			\n	diff			\n	download		\n	edit	
	eth				\n	group			\n	grub			\n	hdd		
	help			\n	history			\n	info			\n	install	
	link			\n	list			\n	locale			\n	lock	
	logs			\n	loopback		\n	modules			\n	ok		
	proc			\n	refresh			\n	removable		\n	remove	
	repack			\n	report			\n	restart			\n	run		
	save			\n	scan			\n	settings		\n	start	
	stop			\n	sync			\n	tag				\n	tags	
	tazx			\n	temperature		\n	terminal		\n	text	
	unlink			\n	unlock			\n	upgrade			\n	user	
	view			\n	wifi			\n	man				\n	off		
	on				\n	opt				\n	web				\n	slitaz	
	lvl0			\n	lvl1			\n	lvl2			\n	lvl3	
	lvl4			\n	lvl5			\n	online			\n	offline	
	sechi			\n	secmi			\n	seclo			\n	pkg		
	pkgi			\n	pkgib			\n	toggle			\n	chlock	
	calendar		\n	modem			\n	cpu				\n	display	
	msg				\n	msgerr			\n	msgwarn			\n	msgup	
	msgtip			\n	vpn			" | \
	while read icon symbol; do
		echo -n "s|data-icon=\"$icon\"|data-icon=\"$symbol\"|g; " >> "$sed_script"
		echo -n "s|data_icon=\"$icon\"|data_icon=\"$symbol\"|g; " >> "$sed_script"
		echo -n "s|repo_icon=\"$icon\"|repo_icon=\"$symbol\"|g; " >> "$sed_script"
		case $icon in
			clock)
				echo -n "s|dataset\.icon==\"$icon\"|dataset.icon==\"$symbol\"|g; " >> "$sed_script";;
			pkg|pkgi|pkgib)
				echo -n "s|data-icon=\\\\\"$icon\\\\\"|data-icon=\\\\\"$symbol\\\\\"|g; " >> "$sed_script";;
		esac
		echo -n "s|data-img=\"$icon\"|data-img=\"$symbol\"|g; " >> "$sed_script"
	done
	echo "' @@@" >> "$sed_script"


cd build

echo -e "\nStrip shell scripts"
for CGI in $(ls | grep -v \.css$ | grep -v \.js$); do
	echo "Processing $CGI"

	mv $CGI $CGI.old
	# Copy initial comment (down to empty line)
	sed '1,/^$/!d' $CGI.old > $CGI
	# Remove initial tabs, other comments and empty lines
	sed 's|^\t*||;/^ *#/d;/^$/d' $CGI.old >> $CGI
	rm $CGI.old

	substitute_icons $CGI

	sed -i 's|" *>|">|g' $CGI
	sed -i "s|' *)|')|g" $CGI
	sed -i 's| *;;|;;|g' $CGI

	chmod a+x $CGI

done


echo -e "\n\nStrip CSS stylesheets"
for CSS in *.css; do
	echo "Processing $CSS"

	mv $CSS $CSS.old
	tr '\n' ' ' < $CSS.old > $CSS
	rm $CSS.old

	substitute_icons $CSS

	sed -i 's|\t| |g; s|  *| |g; s|/\*|‹|g; s|\*/|›|g; s|‹[^›][^›]*›||g; s|  *| |g; s|^ ||; s| {|{|g; s|{ |{|g; s| *: *|:|g; s| *; *|;|g; s|;}|}|g; s|} |}|g; s| *> *|>|g; s| *, *|,|g; s|000000|000|g; s|CC0000|C00|g; s|00FFFF|0FF|g' $CSS
done

mkdir gz
cat *.css > gz/pkgs.css
gzip -9 gz/pkgs.css


rm "$sed_script"
echo
