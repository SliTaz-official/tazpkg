#!/bin/sh
#
# TazPkg CGI interface - Manage packages via a browser
#
# This CGI interface extensively uses tazpkg to manage packages and have
# its own code for some tasks. Please KISS, it is important and keep speed
# in mind. Thanks, Pankso.
#
# (C) 2011-2014 SliTaz GNU/Linux - BSD License
#

. /lib/libtaz.sh
. lib/libtazpanel
get_config
header


# xHTML 5 header with special side bar for categories.
TITLE=$(TEXTDOMAIN='tazpkg'; _ 'TazPanel - Packages')
xhtml_header | sed 's/id="content"/id="content-sidebar"/'

export TEXTDOMAIN='tazpkg'
PKGS_DB="$LOCALSTATE"

pkg_info_link()
{
	echo "$SCRIPT_NAME?info=$1" | sed 's/+/%2B/g'
}


i18n_desc() {
	# Display localized short description
	for L in $LANG ${LANG%%_*}; do
		if [ -e "$PKGS_DB/packages-desc.$L" ]; then
			LOCDESC=$(awk -F$'\t' -vp=$pkg '{if ($1 == p) print $2}' $PKGS_DB/packages-desc.$L)
			if [ -n "$LOCDESC" ]; then
				SHORT_DESC="$LOCDESC"
				break
			fi
		fi
	done
}


# We need packages information for list and search

parse_packages_desc() {
	IFS="|"
	cut -f 1,2,3,5 -d "|" | while read PACKAGE VERSION SHORT_DESC WEB_SITE
	do
		image=tazpkg-installed.png
		[ -d $INSTALLED/${PACKAGE% } ] || image=tazpkg.png
		i18n_desc
		cat << EOT
<tr>
<td><input type="checkbox" name="pkg" value="$PACKAGE">
	<a href="$(pkg_info_link $PACKAGE)"><img
		src="$IMAGES/$image"/>$PACKAGE</a></td>
<td>$VERSION</td>
<td class="desc">$SHORT_DESC</td>
<td><a href="$WEB_SITE"><img src="$IMAGES/browser.png"/></a></td>
</tr>
EOT
	done
	unset IFS
}


# Display a full summary of packages stats

packages_summary() {
	cat << EOT
<table class="zebra outbox">
<tbody>
<tr><td>$(_ 'Last recharge:')</td>
EOT
	stat=$(stat -c %y $PKGS_DB/packages.list | \
		sed 's/\(:..\):.*/\1/' | awk '{print $1}')
	mtime=$(find $PKGS_DB/packages.list -mtime +10)
	echo -n "<td>$stat "
	if [ "$mtime" ]; then
		_ '(Older than 10 days)'
	else
		_ '(Not older than 10 days)'
	fi
	cat << EOT
</td></tr>
<tr><td>$(_ 'Installed packages:')</td>
	<td>$(ls $INSTALLED | wc -l)</td></tr>
<tr><td>$(_ 'Mirrored packages:')</td>
	<td>$(cat $PKGS_DB/packages.list | wc -l)</td></tr>
<tr><td>$(_ 'Upgradeable packages:')</td>
	<td>$(cat $PKGS_DB/packages.up | wc -l)</td></tr>
<tr><td>$(_ 'Installed files:')</td>
	<td>$(cat $INSTALLED/*/files.list | wc -l)</td></tr>
<tr><td>$(_ 'Blocked packages:')</td>
	<td>$(cat $PKGS_DB/blocked-packages.list | wc -l)</td></tr>
</tbody>
</table>
EOT
}


# Parse mirrors list to be able to have an icon and remove link

list_mirrors() {
	while read line
	do
		cat << EOT
<li>
	<a href="$SCRIPT_NAME?admin=rm-mirror=$line&amp;file=$(httpd -e $1)">
		<img src="$IMAGES/clear.png" title="$(_ 'Delete')" />
	</a>
	<a href="$SCRIPT_NAME?admin=select-mirror&amp;mirror=$line">
		<img src="$IMAGES/start.png" title="$(_ 'Use as default')" />
	</a>
	<a href="$line">$line</a>
</li>
EOT
	done < $1
}


# Parse repositories list to be able to have an icon and remove link

list_repos() {
	ls $PKGS_DB/undigest 2> /dev/null | while read repo ; do
		cat <<EOT
	<li><a href="$SCRIPT_NAME?admin=rm-repo=$repo">
		<img src="$IMAGES/clear.png">$repo</a></li>
EOT
	done
}



#
# xHTML functions
#


# ENTER will search but user may search for a button, so put one.

search_form() {
	[ -n "$repo" ] || repo="$(GET repo)"
	[ -n "$repo" ] || repo=Any
	cat << EOT
<div class="search">
	<form method="get" action="$SCRIPT_NAME">
		<p>
			<input type="text" name="search" size="20">
			<input type="submit" value="$(gettext 'Search')">
			<input class="radius" type="submit" name="files"
				value="$(_n 'Files')">
			<input type="hidden" name="repo" value="$repo" />
		</p>
	</form>
</div>
EOT
}


table_head() {
	cat << EOT
		<thead>
		<tr>
			<td>$(_ 'Name')</td>
			<td>$(_ 'Version')</td>
			<td>$(_ 'Description')</td>
			<td>$(_ 'Web')</td>
		</tr>
		</thead>
EOT
}


sidebar() {
	[ -n "$repo" ] || repo=Public
	cat << EOT
<div id="sidebar">
	<h4>$(_ 'Categories')</h4>
	<a class="active_base-system"  href="$SCRIPT_NAME?cat=base-system&repo=$repo" >$(_ 'base-system')</a>
	<a class="active_x-window"     href="$SCRIPT_NAME?cat=x-window&repo=$repo"    >$(_ 'x-window')</a>
	<a class="active_utilities"    href="$SCRIPT_NAME?cat=utilities&repo=$repo"   >$(_ 'utilities')</a>
	<a class="active_network"      href="$SCRIPT_NAME?cat=network&repo=$repo"     >$(_ 'network')</a>
	<a class="active_games"        href="$SCRIPT_NAME?cat=games&repo=$repo"       >$(_ 'games')</a>
	<a class="active_graphics"     href="$SCRIPT_NAME?cat=graphics&repo=$repo"    >$(_ 'graphics')</a>
	<a class="active_office"       href="$SCRIPT_NAME?cat=office&repo=$repo"      >$(_ 'office')</a>
	<a class="active_multimedia"   href="$SCRIPT_NAME?cat=multimedia&repo=$repo"  >$(_ 'multimedia')</a>
	<a class="active_development"  href="$SCRIPT_NAME?cat=development&repo=$repo" >$(_ 'development')</a>
	<a class="active_system-tools" href="$SCRIPT_NAME?cat=system-tools&repo=$repo">$(_ 'system-tools')</a>
	<a class="active_security"     href="$SCRIPT_NAME?cat=security&repo=$repo"    >$(_ 'security')</a>
	<a class="active_misc"         href="$SCRIPT_NAME?cat=misc&repo=$repo"        >$(_ 'misc')</a>
	<a class="active_meta"         href="$SCRIPT_NAME?cat=meta&repo=$repo"        >$(_ 'meta')</a>
	<a class="active_non-free"     href="$SCRIPT_NAME?cat=non-free&repo=$repo"    >$(_ 'non-free')</a>
	<a class="active_all"          href="$SCRIPT_NAME?cat=all&repo=$repo"         >$(_ 'all')</a>
	<a class="active_extra"        href="$SCRIPT_NAME?cat=extra&repo=$repo"       >$(_ 'extra')</a>
EOT

	if [ -d $PKGS_DB/undigest ]; then
		[ -n "$category" ] || category="base-system"
		cat << EOT
	<h4>$(_ 'Repositories')</h4>
	<a class="repo_Public" href="$SCRIPT_NAME?repo=Public&cat=$category">$(_ 'Public')</a>
EOT

		for i in $(ls $PKGS_DB/undigest); do
			cat << EOT
	<a class="repo_$i" href="$SCRIPT_NAME?repo=$i&cat=$category">$i</a>
EOT
		done

		cat << EOT
	<a class="repo_Any" href="$SCRIPT_NAME?repo=Any&cat=$category">$(_ 'Any')</a>
EOT
	fi
	echo "</div>"
}


repo_list() {
	if [ -n "$(ls $PKGS_DB/undigest/ 2> /dev/null)" ]; then
		case "$repo" in
			Public)
				;;
			""|Any)
				for i in $PKGS_DB/undigest/* ; do
					[ -d "$i" ] && echo "$i$1"
				done ;;
			*)
				echo "$PKGS_DB/undigest/$repo$1"
				return ;;
		esac
	fi
	echo "$PKGS_DB$1"
}


repo_name() {
	case "$1" in
		$PKGS_DB)
			echo "Public" ;;
		$PKGS_DB/undigest/*)
			echo ${1#$PKGS_DB/undigest/} ;;
	esac
}



#
# Commands
#


case " $(GET) " in
	*\ list\ *)
		#
		# List installed packages. This is the default because parsing
		# the full packages.desc can be long and take up some resources
		#
		cd $INSTALLED
		search_form
		sidebar
		LOADING_MSG="$(_ 'Listing packages...')"
		loading_msg
		cat << EOT
<h2>$(_ 'My packages')</h2>
<form method='get' action='$SCRIPT_NAME'>
	<input type="hidden" name="do" value="Remove" />
<div id="actions">
	<div class="float-left">
		$(_ 'Selection:')
		<input type="submit" value="$(_ 'Remove')" />
	</div>
	<div class="float-right">
		<a class="button" href="$SCRIPT_NAME?recharge">
			<img src="$IMAGES/recharge.png" />$(_ 'Recharge list')</a>
		<a class="button" href='$SCRIPT_NAME?up'>
			<img src="$IMAGES/update.png" />$(_ 'Check upgrades')</a>
	</div>
</div>
EOT
		cat << EOT
<table class="zebra outbox">
$(table_head)
<tbody>
EOT
		for pkg in *; do
			. $pkg/receipt
			echo '<tr>'
			# Use default tazpkg icon since all packages displayed are
			# installed
			colorpkg=$pkg
			grep -qs "^$pkg$" $PKGS_DB/blocked-packages.list &&
				colorpkg="<span style='color: red;'>$pkg</span>"
			i18n_desc
			cat << EOT
<td class="pkg">
	<input type="checkbox" name="pkg" value="$pkg" />
		<a href="$(pkg_info_link $pkg)"><img
			src="$IMAGES/tazpkg-installed.png"/>$colorpkg</a></td>
<td>$VERSION</td>
<td class="desc">$SHORT_DESC</td>
<td><a href="$WEB_SITE"><img src="$IMAGES/browser.png"/></a></td>
</tr>
EOT
		done
		cat << EOT
</tbody>
</table>
</form>
EOT
		;;


	*\ linkable\ *)
		#
		# List linkable packages.
		#
		cd $INSTALLED
		search_form
		sidebar
		LOADING_MSG=$(_ 'Listing linkable packages...')
		loading_msg
		cat << EOT
<h2>$(_ 'Linkable packages')</h2>

<form method='get' action='$SCRIPT_NAME'>
	<input type="hidden" name="do" value="Link" />
<div id="actions">
	<div class="float-left">
		$(_ 'Selection:')
		<input type="submit" value="$(_ 'Link')" />
	</div>
	<div class="float-right">
		<a class="button" href="$SCRIPT_NAME?recharge">
			<img src="$IMAGES/recharge.png" />$(_ 'Recharge list')</a>
		<a class="button" href="$SCRIPT_NAME?up">
			<img src="$IMAGES/update.png" />$(_ 'Check upgrades')</a>
	</div>
</div>
EOT
		cat << EOT
<table class="zebra outbox">
$(table_head)
<tbody>
EOT
		target=$(readlink $PKGS_DB/fslink)
		for pkg in $(ls $target/$INSTALLED); do
			[ -s $pkg/receipt ] && continue
			. $target/$INSTALLED/$pkg/receipt
			i18n_desc
			cat << EOT
<tr>
	<td class="pkg">
		<input type="checkbox" name="pkg" value="$pkg" />
			<a href="$(pkg_info_link $pkg)"><img
				src="$IMAGES/tazpkg.png"/>$pkg</a>
	</td>
	<td>$VERSION</td>
	<td class="desc">$SHORT_DESC</td>
	<td><a href="$WEB_SITE"><img src="$IMAGES/browser.png"/></a></td>
</tr>
EOT
		done
		cat << EOT
</tbody>
</table>
</form>
EOT
		;;


	*\ cat\ *)
		#
		# List all available packages by category on mirror. Listing all
		# packages is too resource intensive and not useful.
		#
		cd  $PKGS_DB
		repo=$(GET repo)
		category=$(GET cat)
		[ "$category" == "cat" ] && category="base-system"
		grep_category=$category
		[ "$grep_category" == "all" ] && grep_category=".*"
		search_form
		sidebar | sed "s/active_$category/active/;s/repo_$repo/active/"
		LOADING_MSG="$(_ 'Listing packages...')"
		loading_msg
		cat << EOT
<h2>$(_ 'Category: %s' $category)</h2>

<form method='get' action='$SCRIPT_NAME'>
<div id="actions">
<div class="float-left">
	$(_ 'Selection:')
	<input type="submit" name="do" value="Install" />
	<input type="submit" name="do" value="Remove" />
	<input type="hidden" name="repo" value="$repo" />
</div>
<div class="float-right">
	<a class="button" href="$SCRIPT_NAME?recharge">
		<img src="$IMAGES/recharge.png" />$(_ 'Recharge list')</a>
	<a class="button" href="$SCRIPT_NAME?up">
		<img src="$IMAGES/update.png" />$(_ 'Check upgrades')</a>
	<a class="button" href='$SCRIPT_NAME?list'>
		<img src="$IMAGES/tazpkg.png" />$(_ 'My packages')</a>
</div>
</div>
EOT
		for i in $(repo_list ""); do
			if [ "$repo" != "Public" ]; then
				Repo_Name="$(repo_name $i)"
				cat << EOT
<h3>$(_ 'Repository: %s' $Repo_Name)</h3>
EOT
			fi
			cat << EOT
<table class="zebra outbox">
$(table_head)
<tbody>
EOT
			if [ "$category" == "extra" ]; then
				sed 's,.*,&|--|--|--|http://mirror.slitaz.org/packages/get/&,' $i/extra.list
			else
				grep "| $grep_category |" $i/packages.desc
			fi | parse_packages_desc
			cat << EOT
</tbody>
</table>
EOT
		done
		echo '</form>' ;;


	*\ search\ *)
		#
		# Search for packages. Here default is to search in packages.desc
		# and so get result including packages names and descriptions
		#
		pkg=$(GET search)
		repo=$(GET repo)
		cd  $PKGS_DB
		search_form
		sidebar | sed "s/repo_$repo/active/"
		LOADING_MSG="$(_ 'Searching packages...')"
		loading_msg
		cat << EOT
<h2>$(_ 'Search packages')</h2>
<form method="get" action="$SCRIPT_NAME">
<div id="actions">
<div class="float-left">
	$(_ 'Selection:')
	<input type="submit" name="do" value="Install" />
	<input type="submit" name="do" value="Remove" />
	<a href="$(cat $PANEL/lib/checkbox.js)">$(_ 'Toogle all')</a>
</div>
<div class="float-right">
	<a class="button" href="$SCRIPT_NAME?recharge">
		<img src="$IMAGES/recharge.png" />$(_ 'Recharge list')</a>
	<a class="button" href="$SCRIPT_NAME?up">
		<img src="$IMAGES/update.png" />$(_ 'Check upgrades')</a>
	<a class="button" href='$SCRIPT_NAME?list'>
		<img src="$IMAGES/tazpkg.png" />$(_ 'My packages')</a>
</div>
</div>
	<input type="hidden" name="repo" value="$repo" />

	<table class="zebra outbox">
EOT
		if [ "$(GET files)" ]; then
			cat <<EOT
	<thead>
		<tr>
			<td>$(_ 'Package')</td>
			<td>$(_ 'File')</td>
		</tr>
	<thead>
	<tbody>
EOT
			unlzma -c $(repo_list /files.list.lzma) \
				| grep -Ei ": .*$(GET search)" | \
				while read PACKAGE FILE; do
					PACKAGE=${PACKAGE%:}
					image=tazpkg-installed.png
					[ -d $INSTALLED/$PACKAGE ] || image=tazpkg.png
					cat << EOT
<tr>
	<td><input type="checkbox" name="pkg" value="$PACKAGE">
		<a href="$(pkg_info_link $PACKAGE)"><img src="$IMAGES/$image" />$PACKAGE</a></td>
	<td>$FILE</td>
</tr>
EOT
				done
		else
			cat << EOT
$(table_head)
	<tbody>
EOT
			grep -ih $pkg $(repo_list /packages.desc) | \
				parse_packages_desc
		fi
		cat << EOT
	</tbody>
	</table>
</form>
EOT
		;;


	*\ recharge\ *)
		#
		# Lets recharge the packages list
		#
		search_form
		sidebar
		LOADING_MSG="$(_ 'Recharging lists...')"
		loading_msg
		cat << EOT
<h2>$(_ 'Recharge')</h2>

<form method='get' action='$SCRIPT_NAME'>
<div id="actions">
	<div class="float-left">
		<p>$(_ 'Recharge checks for new or updated packages')</p>
	</div>
	<div class="float-right">
		<a class="button" href='$SCRIPT_NAME?up'>
			<img src="$IMAGES/update.png" />$(_ 'Check upgrades')</a>
		<a class="button" href='$SCRIPT_NAME?list'>
			<img src="$IMAGES/tazpkg.png" />$(_ 'My packages')</a>
	</div>
</div>
<div class="wrapper">
<pre>
EOT
		echo $(_ 'Recharging packages list') | log
		tazpkg recharge | filter_taztools_msgs
		cat << EOT
</pre>
</div>
<p>$(_ 'Packages lists are up-to-date. You should check for upgrades now.')</p>
EOT
		;;


	*\ up\ *)
		#
		# Upgrade packages
		#
		cd $PKGS_DB
		search_form
		sidebar
		LOADING_MSG="$(_ 'Checking for upgrades...')"
		loading_msg
		cat << EOT
<h2>$(_ 'Up packages')</h2>

<form method="get" action="$SCRIPT_NAME">
<div id="actions">
	<div class="float-left">
		$(_ 'Selection:')
		<input type="submit" name="do" value="Install" />
		<input type="submit" name="do" value="Remove" />
		<a href="$(cat $PANEL/lib/checkbox.js)">$(_ 'Toogle all')</a>
	</div>
	<div class="float-right">
		<a class="button" href="$SCRIPT_NAME?recharge">
			<img src="$IMAGES/recharge.png" />$(_ 'Recharge list')</a>
		<a class="button" href="$SCRIPT_NAME?list">
			<img src="$IMAGES/tazpkg.png" />$(_ 'My packages')</a>
	</div>
</div>
EOT
		tazpkg up --check >/dev/null
		cat << EOT
<table class="zebra outbox">
$(table_head)
<tbody>
EOT
		for pkg in `cat packages.up`
		do
			grep -hs "^$pkg |" $PKGS_DB/packages.desc \
				$PKGS_DB/undigest/*/packages.desc | \
				parse_packages_desc
		done
		cat << EOT
</tbody>
</table>
</form>
EOT
		;;


	*\ do\ *)
		#
		# Do an action on one or some packages
		#
		opt=""
		pkgs=""
		cmdline=$(echo ${QUERY_STRING#do=} | sed s'/&/ /g')
		cmd=$(echo ${cmdline} | awk '{print $1}')
		cmdline=${cmdline#*repo=* }
		pkgs=$(echo $cmdline | sed -e s'/+/ /g' -e s'/pkg=//g' -e s/$cmd//)
		pkgs="$(httpd -d "$pkgs")"
		cmd=$(echo $cmd | tr [:upper:] [:lower:])
		case $cmd in
			install)
				cmd=get-install opt=--forced
				LOADING_MSG="get-installing packages..."
				;;
			link)
				opt=$(readlink $PKGS_DB/fslink)
				LOADING_MSG="linking packages..."
				;;
		esac
		search_form
		sidebar
		loading_msg
		cat << EOT
<h2>TazPkg: $cmd</h2>

<form method="get" action="$SCRIPT_NAME">
<div id="actions">
	<div class="float-left">
		<p>$(_ 'Performing tasks on packages')</p>
	</div>
	<div class="float-right">
		<p>
			<a class="button" href="$SCRIPT_NAME?list">
				<img src="$IMAGES/tazpkg.png" />$(_ 'My packages')</a>
		</p>
	</div>
</div>
<div class="box">
$(_ 'Executing %s for: %s' $cmd $pkgs)
</div>
EOT
		for pkg in $pkgs; do
			echo '<pre>'
				echo $(_n 'y') | tazpkg $cmd $pkg $opt 2>/dev/null | filter_taztools_msgs
			echo '</pre>'
		done ;;


	*\ info\ *)
		#
		# Packages info
		#
		pkg=$(GET info)
		search_form
		sidebar
		if [ -d $INSTALLED/$pkg ]; then
			. $INSTALLED/$pkg/receipt
			files=$(cat $INSTALLED/$pkg/files.list | wc -l)
			action="Remove"
			action_i18n=$(_ 'Remove')
		else
			cd  $PKGS_DB
			LOADING_MSG=$(_ 'Getting package info...')
			loading_msg
			IFS='|'
			set -- $(grep -hs "^$pkg |" packages.desc undigest/*/packages.desc)
			unset IFS
			PACKAGE=$1
			VERSION="$(echo $2)"
			SHORT_DESC="$(echo $3)"
			CATEGORY="$(echo $4)"
			WEB_SITE="$(echo $5)"
			action="Install"
			action_i18n=$(_ 'Install')
			temp="$(echo $pkg | sed 's/get-//g')"
		fi
		cat << EOT
<h2>$(_ 'Package %s' $PACKAGE)</h2>

<div id="actions">
	<div class="float-left">
		<p>
EOT
		if [ "$temp" != "$pkg" -a "$action" == "Install" ]; then
			temp="$(echo $pkg | sed 's/get-//g')"
			echo "<a class='button' href='$SCRIPT_NAME?do=Install&$temp'>$(_ 'Install (Non Free)')</a>"
		else
			echo "<a class='button' href='$SCRIPT_NAME?do=$action&$pkg'>$action_i18n</a>"
		fi

		if [ -d $INSTALLED/$pkg ]; then
			if grep -qs "^$pkg$" $PKGS_DB/blocked-packages.list; then
				cat << EOT
			<a class="button" href="$SCRIPT_NAME?do=Unblock&$pkg">$(_ 'Unblock')</a>
EOT
			else
				cat << EOT
			<a class="button" href='$SCRIPT_NAME?do=Block&$pkg'>$(_ 'Block')</a>
EOT
			fi
			cat << EOT
			<a class="button" href='$SCRIPT_NAME?do=Repack&$pkg'>$(_ 'Repack')</a>
EOT
		fi
		i18n_desc
		cat << EOT
		</p>
	</div>
	<div class="float-right">
		<p>
			<a class="button" href='$SCRIPT_NAME?list'>
				<img src="$IMAGES/tazpkg.png" />$(_ 'My packages')</a>
		</p>
	</div>
</div>
<table class="zebra outbox">
<tbody>
	<tr><td><b>$(_ 'Name')</b></td><td>$PACKAGE</td></tr>
	<tr><td><b>$(_ 'Version')</b></td><td>$VERSION</td></tr>
	<tr><td><b>$(_ 'Description')</b></td><td>$SHORT_DESC</td></tr>
	<tr><td><b>$(_ 'Category')</b></td><td>$CATEGORY</td></tr>
EOT
		if [ -d $INSTALLED/$pkg ]; then
			cat << EOT
	<tr><td><b>$(_ 'Maintainer')</b></td><td>$MAINTAINER</td></tr>
	<tr><td><b>$(_ 'Website')</b></td><td><a href="$WEB_SITE">$WEB_SITE</a></td></tr>
	<tr><td><b>$(_ 'Sizes')</b></td><td>$PACKED_SIZE/$UNPACKED_SIZE</td></tr>
EOT
			if [ -n "$DEPENDS" ]; then
				echo "<tr><td><b>$(_ 'Depends')</b></td><td>"
				for i in $DEPENDS; do
					echo -n "<a href="$(pkg_info_link $i)">$i</a> "
				done
				echo "</td></tr>"
			fi
			if [ -n "$SUGGESTED" ]; then
				echo "<tr><td><b>$(_ 'Suggested')</b></td><td>"
				for i in $SUGGESTED; do
					echo -n "<a href="$(pkg_info_link $i)">$i</a> "
				done
				echo "</td></tr>"
			fi
			[ -n "$TAGS" ] && echo "<tr><td><b>$(_ 'Tags')</b></td><td>$TAGS</td></tr>"
			I_FILES=$(cat $INSTALLED/$pkg/files.list | wc -l)
			cat << EOT
</tbody>
</table>
EOT
			DESC="$(tazpkg desc $pkg)"
			[ -n "$DESC" ] && echo "<pre>$DESC</pre>"

			cat << EOT
<p>$(_ 'Installed files: %s' $I_FILES)</p>

<pre>$(sort $INSTALLED/$pkg/files.list)</pre>
EOT
		else
			cat << EOT
<tr><td><b>$(_ 'Website')</b></td><td><a href="$WEB_SITE">$WEB_SITE</a></td></tr>
<tr><td><b>$(_ 'Sizes')</b></td><td>$(grep -hsA 3 ^$pkg$ packages.txt undigest/*/packages.txt | \
		tail -n 1 | sed 's/ *//')</td></tr>
</table>

<p>$(_ 'Installed files:')</p>

<pre>
$(lzcat files.list.lzma undigest/*/files.list.lzma 2> /dev/null | \
 sed "/^$pkg: /!d;s/^$pkg: //" | sort)
</pre>
EOT
		fi
		;;


	*\ admin\ * )
		#
		# TazPkg configuration page
		#
		cmd=$(GET admin)
		case "$cmd" in
			clean)
				rm -rf /var/cache/tazpkg/* ;;
			add-mirror)
				# Decode url
				mirror=$(GET mirror)
				case "$mirror" in
				http://*|ftp://*)
					echo "$mirror" >> $(GET file) ;;
				esac ;;
			rm-mirror=http://*|rm-mirror=ftp://*)
				mirror=${cmd#rm-mirror=}
				sed -i -e "s@$mirror@@" -e '/^$/d' $(GET file) ;;
			select-mirror*)
				release=$(cat /etc/slitaz-release)
				mirror="$(GET mirror)packages/$release/"
				tazpkg setup-mirror $mirror | log
				;;
			add-repo)
				# Decode url
				mirror=$(GET mirror)
				repository=$PKGS_DB/undigest/$(GET repository)
				case "$mirror" in
				http://*|ftp://*)
					mkdir -p $repository
					echo "$mirror" > $repository/mirror
					echo "$mirror" > $repository/mirrors ;;
				esac ;;
			rm-repo=*)
				repository=${cmd#rm-repo=}
				rm -rf $PKGS_DB/undigest/$repository ;;
		esac
		[ "$cmd" == "$(_n 'Set link')" ] &&
			[ -d "$(GET link)/$INSTALLED" ] &&
			ln -fs $(GET link) $PKGS_DB/fslink
		[ "$cmd" == "$(_n 'Remove link')" ] &&
			rm -f $PKGS_DB/fslink
		cache_files=$(find /var/cache/tazpkg -name *.tazpkg | wc -l)
		cache_size=$(du -sh /var/cache/tazpkg | cut -f1 | sed 's|\.0||')
		sidebar
		cat << EOT
<h2>$(_ 'Administration')</h2>
<div>
	<p>$(_ 'TazPkg administration and settings')</p>
</div>
<div id="actions">
	<a class="button" href='$SCRIPT_NAME?admin=&action=saveconf'>
		<img src="$IMAGES/tazpkg.png" />$(_ 'Save configuration')</a>
	<a class="button" href='$SCRIPT_NAME?admin=&action=listconf'>
		<img src="$IMAGES/edit.png" />$(_ 'List configuration files')</a>
	<a class="button" href='$SCRIPT_NAME?admin=&action=quickcheck'>
		<img src="$IMAGES/recharge.png" />$(_ 'Quick check')</a>
	<a class="button" href='$SCRIPT_NAME?admin=&action=fullcheck'>
		<img src="$IMAGES/recharge.png" />$(_ 'Full check')</a>
</div>
EOT
		case "$(GET action)" in
				saveconf)
					LOADING_MSG=$(_ 'Creating the package...')
					loading_msg
					echo "<pre>"
					cd $HOME
					tazpkg repack-config | filter_taztools_msgs
					echo -n "$(_ 'Path:') "; ls $HOME/config-*.tazpkg
					echo "</pre>" ;;
				listconf)
					echo "<h4>$(_ 'Configuration files')</h4>"
					echo "<ul>"
					tazpkg list-config | while read file; do
						[ "${file:0:1}" == "/" ] || continue
						if [ -e $file ]; then
							echo "<li><a href=\"index.cgi?file=$file\">$file</a></li>"
						else
							echo "<li>$file</li>"
						fi
					done
					echo "</ul>"
					echo "</pre>" ;;
				quickcheck)
					LOADING_MSG=$(_ 'Checking packages consistency...')
					loading_msg
					echo "<pre>"
					tazpkg check
					echo "</pre>" ;;
				fullcheck)
					LOADING_MSG=$(_ 'Full packages check...')
					loading_msg
					echo "<pre>"
					tazpkg check --full
					echo "</pre>" ;;
				esac
		cat << EOT
<h3>$(_ 'Packages cache')</h3>

<div>
	<form method="get" action="$SCRIPT_NAME">
		<p>
			$(_ 'Packages in the cache: %s (%s)' $cache_files $cache_size)
			<input type="hidden" name="admin" value="clean" />
			<input type="submit" value="Clean" />
		</p>
	</form>
</div>

<h3>$(_ 'Default mirror')</h3>

<pre>$(cat /var/lib/tazpkg/mirror)</pre>

<h3>$(_ 'Current mirror list')</h3>
EOT
		for i in $PKGS_DB/mirrors $PKGS_DB/undigest/*/mirrors; do
			[ -s $i ] || continue
			echo '<div class="box">'
			if [ $i != $PKGS_DB/mirrors ]; then
				Repo_Name="$(repo_name $(dirname $i))"
				echo "<h4>$(_ 'Repository: %s' $Repo_Name)</h4>"
			fi
			echo "<ul>"
			list_mirrors $i
			echo "</ul>"
			cat << EOT
</div>
<form method="get" action="$SCRIPT_NAME">
	<p>
		<input type="hidden" name="admin" value="add-mirror" />
		<input type="hidden" name="file" value="$i" />
		<input type="text" name="mirror" size="60">
		<input type="submit" value="Add mirror" />
	</p>
</form>
EOT
		done
		echo "<h3>$(_ 'Private repositories')</h3>"
		[ -n "$(ls $PKGS_DB/undigest 2> /dev/null)" ] && cat << EOT
<div class="box">
	<ul>
		$(list_repos)
	</ul>
</div>
EOT
		cat << EOT
<form method="get" action="$SCRIPT_NAME">
	<p>
		<input type="hidden" name="admin" value="add-repo" />
		$(_ 'Name') <input type="text" name="repository" size="10">
		$(_ 'mirror')
		<input type="text" name="mirror" value="http://" size="50">
		<input type="submit" value="Add repository" />
	</p>
</form>

<h3>$(_ 'Link to another SliTaz installation')</h3>

<p>$(_ "This link points to the root of another SliTaz installation. \
You will be able to install packages using soft links to it.")</p>

<form method="get" action="$SCRIPT_NAME">
<p>
	<input type="hidden" name="admin" value="add-link" />
	<input type="text" name="link"
	 value="$(readlink $PKGS_DB/fslink 2> /dev/null)" size="50">
	<input type="submit" name="admin" value="$(_ 'Set link')" />
	<input type="submit" name="admin" value="$(_ 'Remove link')" />
</p>
</form>
EOT
		version=$(cat /etc/slitaz-release)
		cat << EOT

<h3 id="dvd">$(_ 'SliTaz packages DVD')</h3>

<p>$(_ "A bootable DVD image of all available packages for the %s version is \
generated every day. It also contains a copy of the website and can be used \
without an internet connection. This image can be installed on a DVD or a USB \
key." $version)</p>

<div>
	<form method="post" action='$SCRIPT_NAME?admin&action=dvdimage#dvd'>
	<p>
		<a class="button"
			href='http://mirror.slitaz.org/iso/$version/packages-$version.iso'>
			<img src="$IMAGES/tazpkg.png" />$(_ 'Download DVD image')</a>
		<a class="button" href='$SCRIPT_NAME?admin&action=dvdusbkey#dvd'>
			<img src="$IMAGES/tazpkg.png" />$(_ 'Install from DVD/USB key')</a>
	</p>
	<div class="box">
		$(_ 'Install from ISO image:')
		<input type="text" name="dvdimage" size="40" value="/root/packages-$version.iso">
	</div>
	</form>
</div>
EOT
		if [ "$(GET action)" == "dvdimage" ]; then
			dev=$(POST dvdimage)
			mkdir -p /mnt/packages 2> /dev/null
			echo "<pre>"
			mount -t iso9660 -o loop,ro $dev /mnt/packages &&
			/mnt/packages/install.sh &&
			_ '%s is installed on /mnt/packages' $dev
			echo "</pre>"
		fi
		if [ "$(GET action)" == "dvdusbkey" ]; then
			mkdir -p /mnt/packages 2> /dev/null
			for tag in "LABEL=\"packages-$version\" TYPE=\"iso9660\"" \
				"LABEL=\"sources-$version\" TYPE=\"iso9660\"" ; do
				dev=$(blkid | grep "$tag" | cut -d: -f1)
				[ -n "$dev" ] || continue
				echo "<pre>"
				mount -t iso9660 -o ro $dev /mnt/packages &&
				/mnt/packages/install.sh &&
				_ '%s is installed on /mnt/packages' $dev
				echo "</pre>"
				break
			done
		fi
		 ;;
	*)
		#
		# Default to summary
		#
		search_form
		sidebar
		[ -n "$(GET block)" ] && tazpkg block $(GET block)
		[ -n "$(GET unblock)" ] && tazpkg unblock $(GET unblock)
		cat << EOT
<h2>$(_ 'Summary')</h2>

<div id="actions">
	<a class="button" href="$SCRIPT_NAME?list">
		<img src="$IMAGES/tazpkg.png" />$(_ 'My packages')</a>
EOT
		fslink=$(readlink $PKGS_DB/fslink)
		[ -n "$fslink" -a -d "$fslink/$INSTALLED" ] &&
			cat << EOT
	<a class="button" href="$SCRIPT_NAME?linkable">
		<img src="$IMAGES/tazpkg.png" />$(_ 'Linkable packages')</a>
EOT
		cat << EOT
	<a class="button" href="$SCRIPT_NAME?recharge">
		<img src="$IMAGES/recharge.png" />$(_ 'Recharge list')</a>
	<a class="button" href="$SCRIPT_NAME?up">
		<img src="$IMAGES/update.png" />$(_ 'Check upgrades')</a>
	<a class="button" href="$SCRIPT_NAME?admin">
		<img src="$IMAGES/edit.png" />$(_ 'Administration')</a>
</div>

$(packages_summary)


<h3>$(_ 'Latest log entries')</h3>

<pre>
$(tail -n 5 /var/log/slitaz/tazpkg.log | fgrep "-" | \
	awk '{print $1, $2, $3, $4, $5, $6, $7}')
</pre>
EOT
		;;
esac

# xHTML 5 footer
export TEXTDOMAIN='tazpkg'
xhtml_footer
exit 0
