#!/bin/sh
#
# TazPKG CGI interface - Manage packages via a browser
#
# This CGI interface extensively uses tazpkg to manage packages and have
# its own code for some tasks. Please KISS, it is important and keep speed
# in mind. Thanks, Pankso.
#
# (C) 2011 SliTaz GNU/Linux - BSD License
#

. lib/libtazpanel
get_config
header

# xHTML 5 header with special side bar for categories.
TITLE=$(gettext 'TazPanel - Packages')
xhtml_header | sed 's/id="content"/id="content-sidebar"/'

pkg_info_link()
{
	echo "$SCRIPT_NAME?info=$1" | sed 's/+/%2B/g'
}

i18n_desc() {
	# Display localized short description
	if [ -e "$LOCALSTATE/packages-desc.$LANG" ]; then
		LOCDESC=$(grep -e "^$pkg	" $LOCALSTATE/packages-desc.$LANG | cut -d'	' -f2)
	[ "x$LOCDESC" != "x" ] && SHORT_DESC="$LOCDESC"
	fi
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
<tr><td>$(gettext 'Last recharge:')</td>
EOT
	stat=$(stat -c %y $LOCALSTATE/packages.list | \
		sed 's/\(:..\):.*/\1/' | awk '{print $1}')
	mtime=$(find $LOCALSTATE/packages.list -mtime +10)
	echo -n "<td>$stat "
	if [ "$mtime" ]; then
		gettext '(Older than 10 days)'; echo
	else
		gettext '(Not older than 10 days)'; echo
	fi
	cat << EOT
</td></tr>
<tr><td>$(gettext 'Installed packages:')</td>
	<td>$(ls $INSTALLED | wc -l)</td></tr>
<tr><td>$(gettext 'Mirrored packages:')</td>
	<td>$(cat $LOCALSTATE/packages.list | wc -l)</td></tr>
<tr><td>$(gettext 'Upgradeable packages:')</td>
	<td>$(cat $LOCALSTATE/packages.up | wc -l)</td></tr>
<tr><td>$(gettext 'Installed files:')</td>
	<td>$(cat $INSTALLED/*/files.list | wc -l)</td></tr>
<tr><td>$(gettext 'Blocked packages:')</td>
	<td>$(cat $LOCALSTATE/blocked-packages.list | wc -l)</td></tr>
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
		<img src="$IMAGES/clear.png" title="$(gettext 'Delete')" />
	</a>
	<a href="$SCRIPT_NAME?admin=select-mirror&amp;mirror=$line">
		<img src="$IMAGES/start.png" title="$(gettext 'Use as default')" />
	</a>
	<a href="$line">$line</a>
</li>
EOT
	done < $1
}

# Parse repositories list to be able to have an icon and remove link
list_repos() {
	ls $LOCALSTATE/undigest 2> /dev/null | while read repo ; do
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
				value="$(gettext 'Files')">
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
			<td>$(gettext 'Name')</td>
			<td>$(gettext 'Version')</td>
			<td>$(gettext 'Description')</td>
			<td>$(gettext 'Web')</td>
		</tr>
		</thead>
EOT
}

sidebar() {
	[ -n "$repo" ] || repo=Public
	cat << EOT
<div id="sidebar">
	<h4>$(gettext 'Categories')</h4>
	<a class="active_base-system" href="$SCRIPT_NAME?cat=base-system&repo=$repo">$(gettext 'Base-system')</a>
	<a class="active_x-window" href="$SCRIPT_NAME?cat=x-window&repo=$repo">$(gettext 'X window')</a>
	<a class="active_utilities" href="$SCRIPT_NAME?cat=utilities&repo=$repo">$(gettext 'Utilities')</a>
	<a class="active_network" href="$SCRIPT_NAME?cat=network&repo=$repo">$(gettext 'Network')</a>
	<a class="active_games" href="$SCRIPT_NAME?cat=games&repo=$repo">$(gettext 'Games')</a>
	<a class="active_graphics" href="$SCRIPT_NAME?cat=graphics&repo=$repo">$(gettext 'Graphics')</a>
	<a class="active_office" href="$SCRIPT_NAME?cat=office&repo=$repo">$(gettext 'Office')</a>
	<a class="active_multimedia" href="$SCRIPT_NAME?cat=multimedia&repo=$repo">$(gettext 'Multimedia')</a>
	<a class="active_development" href="$SCRIPT_NAME?cat=development&repo=$repo">$(gettext 'Development')</a>
	<a class="active_system-tools" href="$SCRIPT_NAME?cat=system-tools&repo=$repo">$(gettext 'System tools')</a>
	<a class="active_security" href="$SCRIPT_NAME?cat=security&repo=$repo">$(gettext 'Security')</a>
	<a class="active_misc" href="$SCRIPT_NAME?cat=misc&repo=$repo">$(gettext 'Misc')</a>
	<a class="active_meta" href="$SCRIPT_NAME?cat=meta&repo=$repo">$(gettext 'Meta')</a>
	<a class="active_non-free" href="$SCRIPT_NAME?cat=non-free&repo=$repo">$(gettext 'Non free')</a>
	<a class="active_all" href="$SCRIPT_NAME?cat=all&repo=$repo">$(gettext 'All')</a>
EOT

	if [ -d $LOCALSTATE/undigest ]; then
		[ -n "$category" ] || category="base-system"
		cat << EOT
	<h4>$(gettext 'Repositories')</h4>
	<a class="repo_Public" href="$SCRIPT_NAME?repo=Public&cat=$category">$(gettext 'Public')</a>
EOT
		for i in $(ls $LOCALSTATE/undigest); do
			cat << EOT
	<a class="repo_$i" href="$SCRIPT_NAME?repo=$i&cat=$category">$i</a>
EOT
		done
		cat << EOT
	<a class="repo_Any" href="$SCRIPT_NAME?repo=Any&cat=$category">$(gettext 'Any')</a>
EOT
	fi
	echo "</div>"
}

repo_list() {
	if [ -n "$(ls $LOCALSTATE/undigest/ 2> /dev/null)" ]; then
		case "$repo" in
		Public)	;;
		""|Any) for i in $LOCALSTATE/undigest/* ; do
				[ -d "$i" ] && echo "$i$1"
			done ;;
		*)	echo "$LOCALSTATE/undigest/$repo$1"
			return ;;
		esac
	fi
	echo "$LOCALSTATE$1"
}

repo_name() {
	case "$1" in
	$LOCALSTATE)		echo "Public" ;;
	$LOCALSTATE/undigest/*)	echo ${1#$LOCALSTATE/undigest/} ;;
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
		LOADING_MSG="$(gettext 'Listing packages...')"
		loading_msg
		cat << EOT
<h2>$(gettext 'My packages')</h2>
<form method='get' action='$SCRIPT_NAME'>
	<input type="hidden" name="do" value="Remove" />
<div id="actions">
	<div class="float-left">
		$(gettext 'Selection:')
		<input type="submit" value="$(gettext 'Remove')" />
	</div>
	<div class="float-right">
		<a class="button" href="$SCRIPT_NAME?recharge">
			<img src="$IMAGES/recharge.png" />$(gettext 'Recharge list')</a>
		<a class="button" href='$SCRIPT_NAME?up'>
			<img src="$IMAGES/update.png" />$(gettext 'Check upgrades')</a>
	</div>
</div>
EOT
		cat << EOT
<table class="zebra outbox">
$(table_head)
<tbody>
EOT
		for pkg in *
		do
			. $pkg/receipt
			echo '<tr>'
			# Use default tazpkg icon since all packages displayed are
			# installed
			colorpkg=$pkg
			grep -qs "^$pkg$" $LOCALSTATE/blocked-packages.list &&
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
		LOADING_MSG=$(gettext 'Listing linkable packages...')
		loading_msg
		cat << EOT
<h2>$(gettext 'Linkable packages')</h2>

<form method='get' action='$SCRIPT_NAME'>
	<input type="hidden" name="do" value="Link" />
<div id="actions">
	<div class="float-left">
		$(gettext 'Selection:')
		<input type="submit" value="$(gettext 'Link')" />
	</div>
	<div class="float-right">
		<a class="button" href="$SCRIPT_NAME?recharge">
			<img src="$IMAGES/recharge.png" />$(gettext 'Recharge list')</a>
		<a class="button" href="$SCRIPT_NAME?up">
			<img src="$IMAGES/update.png" />$(gettext 'Check upgrades')</a>
	</div>
</div>
EOT
		cat << EOT
<table class="zebra outbox">
$(table_head)
<tbody>
EOT
		target=$(readlink $LOCALSTATE/fslink)
		for pkg in $(ls $target/$INSTALLED)
		do
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
		cd  $LOCALSTATE
		repo=$(GET repo)
		category=$(GET cat)
		[ "$category" == "cat" ] && category="base-system"
		grep_category=$category
		[ "$grep_category" == "all" ] && grep_category=".*"
		search_form
		sidebar | sed "s/active_$category/active/;s/repo_$repo/active/"
		LOADING_MSG="$(gettext 'Listing packages...')"
		loading_msg
		cat << EOT
<h2>$(eval_gettext 'Category: $category')</h2>

<form method='get' action='$SCRIPT_NAME'>
<div id="actions">
<div class="float-left">
	$(gettext 'Selection:')
	<input type="submit" name="do" value="Install" />
	<input type="submit" name="do" value="Remove" />
	<input type="hidden" name="repo" value="$repo" />
</div>
<div class="float-right">
	<a class="button" href="$SCRIPT_NAME?recharge">
		<img src="$IMAGES/recharge.png" />$(gettext 'Recharge list')</a>
	<a class="button" href="$SCRIPT_NAME?up">
		<img src="$IMAGES/update.png" />$(gettext 'Check upgrades')</a>
	<a class="button" href='$SCRIPT_NAME?list'>
		<img src="$IMAGES/tazpkg.png" />$(gettext 'My packages')</a>
</div>
</div>
EOT
		for i in $(repo_list ""); do
			if [ "$repo" != "Public" ]; then
				Repo_Name="$(repo_name $i)"
				cat << EOT
<h3>$(eval_gettext "Repository: \$Repo_Name")</h3>
EOT
			fi
			cat << EOT
<table class="zebra outbox">
$(table_head)
<tbody>
EOT
			grep "| $grep_category |" $i/packages.desc | \
				parse_packages_desc
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
		cd  $LOCALSTATE
		search_form
		sidebar | sed "s/repo_$repo/active/"
		LOADING_MSG="$(gettext 'Searching packages...')"
		loading_msg
		cat << EOT
<h2>$(gettext 'Search packages')</h2>
<form method="get" action="$SCRIPT_NAME">
<div id="actions">
<div class="float-left">
	$(gettext 'Selection:')
	<input type="submit" name="do" value="Install" />
	<input type="submit" name="do" value="Remove" />
	<a href="`cat $PANEL/lib/checkbox.js`">$(gettext 'Toogle all')</a>
</div>
<div class="float-right">
	<a class="button" href="$SCRIPT_NAME?recharge">
		<img src="$IMAGES/recharge.png" />$(gettext 'Recharge list')</a>
	<a class="button" href="$SCRIPT_NAME?up">
		<img src="$IMAGES/update.png" />$(gettext 'Check upgrades')</a>
	<a class="button" href='$SCRIPT_NAME?list'>
		<img src="$IMAGES/tazpkg.png" />$(gettext 'My packages')</a>
</div>
</div>
	<input type="hidden" name="repo" value="$repo" />

	<table class="zebra outbox">
EOT
		if [ "$(GET files)" ]; then
			cat <<EOT
	<thead>
		<tr>
			<td>$(gettext 'Package')</td>
			<td>$(gettext 'File')</td>
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
		LOADING_MSG="$(gettext 'Recharging lists...')"
		loading_msg
		cat << EOT
<h2>$(gettext 'Recharge')</h2>

<form method='get' action='$SCRIPT_NAME'>
<div id="actions">
	<div class="float-left">
		<p>$(gettext 'Recharge checks for new or updated packages')</p>
	</div>
	<div class="float-right">
		<a class="button" href='$SCRIPT_NAME?up'>
			<img src="$IMAGES/update.png" />$(gettext 'Check upgrades')</a>
		<a class="button" href='$SCRIPT_NAME?list'>
			<img src="$IMAGES/tazpkg.png" />$(gettext 'My packages')</a>
	</div>
</div>
<div class="wrapper">
<pre>
EOT
		echo $(gettext 'Recharging packages list') | log
		tazpkg recharge | filter_taztools_msgs
		cat << EOT
</pre>
</div>
<p>$(gettext "Packages lists are up-to-date. You should check for upgrades \
now.")</p>
EOT
		;;


	*\ up\ *)
		#
		# Upgrade packages
		#
		cd $LOCALSTATE
		search_form
		sidebar
		LOADING_MSG="$(gettext 'Checking for upgrades...')"
		loading_msg
		cat << EOT
<h2>$(gettext 'Up packages')</h2>

<form method="get" action="$SCRIPT_NAME">
<div id="actions">
	<div class="float-left">
		$(gettext 'Selection:')
		<input type="submit" name="do" value="Install" />
		<input type="submit" name="do" value="Remove" />
		<a href="$(cat $PANEL/lib/checkbox.js)">$(gettext 'Toogle all')</a>
	</div>
	<div class="float-right">
		<a class="button" href="$SCRIPT_NAME?recharge">
			<img src="$IMAGES/recharge.png" />$(gettext 'Recharge list')</a>
		<a class="button" href="$SCRIPT_NAME?list">
			<img src="$IMAGES/tazpkg.png" />$(gettext 'My packages')</a>
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
			grep -hs "^$pkg |" $LOCALSTATE/packages.desc \
				$LOCALSTATE/undigest/*/packages.desc | \
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
				opt=$(readlink $LOCALSTATE/fslink)
				LOADING_MSG="linking packages..."
				;;
		esac
		search_form
		sidebar
		loading_msg
		cat << EOT
<h2>Tazpkg: $cmd</h2>

<form method="get" action="$SCRIPT_NAME">
<div id="actions">
	<div class="float-left">
		<p>$(gettext 'Performing tasks on packages')</p>
	</div>
	<div class="float-right">
		<p>
			<a class="button" href="$SCRIPT_NAME?list">
				<img src="$IMAGES/tazpkg.png" />$(gettext 'My packages')</a>
		</p>
	</div>
</div>
<div class="box">
$(eval_gettext 'Executing $cmd for: $pkgs')
</div>
EOT
		for pkg in $pkgs
		do
			echo '<pre>'
			    echo $(gettext 'y') | tazpkg $cmd $pkg $opt 2>/dev/null | filter_taztools_msgs
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
			files=`cat $INSTALLED/$pkg/files.list | wc -l`
			action="Remove"
			action_i18n=$(gettext 'Remove')
		else
			cd  $LOCALSTATE
			LOADING_MSG=$(gettext 'Getting package info...')
			loading_msg
			IFS='|'
			set -- $(grep -hs "^$pkg |" packages.desc \
				 undigest/*/packages.desc)
			unset IFS
			PACKAGE=$1
			VERSION="$(echo $2)"
			SHORT_DESC="$(echo $3)"
			CATEGORY="$(echo $4)"
			WEB_SITE="$(echo $5)"
			action="Install"
			action_i18n=$(gettext 'Install')
			temp="$(echo $pkg | sed 's/get-//g')"
		fi
		cat << EOT
<h2>$(eval_gettext 'Package $PACKAGE')</h2>

<div id="actions">
	<div class="float-left">
		<p>
EOT
		if [ "$temp" != "$pkg" -a "$action" == "Install" ]; then
			temp="$(echo $pkg | sed 's/get-//g')"
			echo "<a class='button' href='$SCRIPT_NAME?do=Install&$temp'>$(gettext 'Install (Non Free)')</a>"
		else
			echo "<a class='button' href='$SCRIPT_NAME?do=$action&$pkg'>$action_i18n</a>"
		fi

		if [ -d $INSTALLED/$pkg ]; then
			if grep -qs "^$pkg$" $LOCALSTATE/blocked-packages.list; then
				cat << EOT
			<a class="button" href="$SCRIPT_NAME?do=Unblock&$pkg">$(gettext 'Unblock')</a>
EOT
			else
				cat << EOT
			<a class="button" href='$SCRIPT_NAME?do=Block&$pkg'>$(gettext 'Block')</a>
EOT
			fi
			cat << EOT
			<a class="button" href='$SCRIPT_NAME?do=Repack&$pkg'>$(gettext 'Repack')</a>
EOT
		fi
		i18n_desc
		cat << EOT
		</p>
	</div>
	<div class="float-right">
		<p>
			<a class="button" href='$SCRIPT_NAME?list'>
				<img src="$IMAGES/tazpkg.png" />$(gettext 'My packages')</a>
		</p>
	</div>
</div>
<table class="zebra outbox">
<tbody>
	<tr><td>$(gettext 'Name:')</td><td>$PACKAGE</td></tr>
	<tr><td>$(gettext 'Version:')</td><td>$VERSION</td></tr>
	<tr><td>$(gettext 'Description:')</td><td>$SHORT_DESC</td></tr>
	<tr><td>$(gettext 'Category:')</td><td>$CATEGORY</td></tr>
EOT
		if [ -d $INSTALLED/$pkg ]; then
			cat << EOT
	<tr><td>$(gettext 'Maintainer:')</td><td>$MAINTAINER</td></tr>
	<tr><td>$(gettext 'Website:')</td><td><a href="$WEB_SITE">$WEB_SITE</a></td></tr>
	<tr><td>$(gettext 'Sizes:')</td><td>$PACKED_SIZE/$UNPACKED_SIZE</td></tr>
EOT
			if [ -n "$DEPENDS" ]; then
				echo "<tr><td>$(gettext 'Depends:')</td><td>"
				for i in $DEPENDS; do
					echo -n "<a href="$(pkg_info_link $i)">$i</a> "
				done
				echo "</td></tr>"
			fi
			if [ -n "$SUGGESTED" ]; then
				echo "<tr><td>$(gettext 'Suggested:')</td><td>"
				for i in $SUGGESTED; do
					echo -n "<a href="$(pkg_info_link $i)">$i</a> "
				done
				echo "</td></tr>"
			fi
			[ -n "$TAGS" ] && echo "<tr><td>$(gettext 'Tags:')</td><td>$TAGS</td></tr>"
			I_FILES=$(cat $INSTALLED/$pkg/files.list | wc -l)
			cat << EOT
</tbody>
</table>

<p>$(eval_gettext 'Installed files: $I_FILES')</p>

<pre>$(cat $INSTALLED/$pkg/files.list)</pre>
EOT
		else
			cat << EOT
<tr><td>$(gettext 'Website:')</td><td><a href="$WEB_SITE">$WEB_SITE</a></td></tr>
<tr><td>$(gettext 'Sizes:')</td><td>$(grep -hsA 3 ^$pkg$ packages.txt undigest/*/packages.txt | \
		tail -n 1 | sed 's/ *//')</td></tr>
</table>

<p>$(gettext 'Installed files:')</p>

<pre>
`unlzma -c files.list.lzma undigest/*/files.list.lzma 2> /dev/null | \
 sed "/^$pkg: /!d;s/^$pkg: //"`
</pre>
EOT
		fi
		;;


	*\ admin\ * )
		#
		# Tazpkg configuration page
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
				release=`cat /etc/slitaz-release`
				mirror="$(GET mirror)packages/$release/"
				tazpkg setup-mirror $mirror | log
				;;
			add-repo)
				# Decode url
				mirror=$(GET mirror)
				repository=$LOCALSTATE/undigest/$(GET repository)
				case "$mirror" in
				http://*|ftp://*)
					mkdir -p $repository
					echo "$mirror" > $repository/mirror
					echo "$mirror" > $repository/mirrors ;;
				esac ;;
			rm-repo=*)
				repository=${cmd#rm-repo=}
				rm -rf $LOCALSTATE/undigest/$repository ;;
		esac
		[ "$cmd" == "$(gettext 'Set link')" ] &&
			[ -d "$(GET link)/$INSTALLED" ] &&
			ln -fs $(GET link) $LOCALSTATE/fslink
		[ "$cmd" == "$(gettext 'Remove link')" ] &&
			rm -f $LOCALSTATE/fslink
		cache_files=`find /var/cache/tazpkg -name *.tazpkg | wc -l`
		cache_size=`du -sh /var/cache/tazpkg`
		sidebar
		cat << EOT
<h2>$(gettext 'Administration')</h2>
<div>
	<p>$(gettext 'Tazpkg administration and settings')</p>
</div>
<div id="actions">
	<a class="button" href='$SCRIPT_NAME?admin=&action=saveconf'>
		<img src="$IMAGES/tazpkg.png" />$(gettext 'Save configuration')</a>
	<a class="button" href='$SCRIPT_NAME?admin=&action=listconf'>
		<img src="$IMAGES/edit.png" />$(gettext 'List configuration files')</a>
	<a class="button" href='$SCRIPT_NAME?admin=&action=quickcheck'>
		<img src="$IMAGES/recharge.png" />$(gettext 'Quick check')</a>
	<a class="button" href='$SCRIPT_NAME?admin=&action=fullcheck'>
		<img src="$IMAGES/recharge.png" />$(gettext 'Full check')</a>
</div>
EOT
		case "$(GET action)" in
				saveconf)
					LOADING_MSG=$(gettext 'Creating the package...')
					loading_msg
					echo "<pre>"
					cd $HOME
					tazpkg repack-config | filter_taztools_msgs
					echo -n "$(gettext 'Path:') " && ls $HOME/config-*.tazpkg
					echo "</pre>" ;;
				listconf)
					echo "<h4>$(gettext 'Configuration files')</h4>"
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
					LOADING_MSG=$(gettext 'Checking packages consistency...')
					loading_msg
					echo "<pre>"
					tazpkg check
					echo "</pre>" ;;
				fullcheck)
					LOADING_MSG=$(gettext 'Full packages check...')
					loading_msg
					echo "<pre>"
					tazpkg check --full
					echo "</pre>" ;;
				esac
		cat << EOT
<h3>$(gettext 'Packages cache')</h3>

<div>
	<form method="get" action="$SCRIPT_NAME">
		<p>
			$(eval_gettext 'Packages in the cache: $cache_files ($cache_size)')
			<input type="hidden" name="admin" value="clean" />
			<input type="submit" value="Clean" />
		</p>
	</form>
</div>

<h3>$(gettext 'Default mirror')</h3>

<pre>$(cat /var/lib/tazpkg/mirror)</pre>

<h3>$(gettext 'Current mirror list')</h3>
EOT
		for i in $LOCALSTATE/mirrors $LOCALSTATE/undigest/*/mirrors; do
			[ -s $i ] || continue
			echo '<div class="box">'
			if [ $i != $LOCALSTATE/mirrors ]; then
				Repo_Name="$(repo_name $(dirname $i))"
				echo "<h4>$(eval_gettext 'Repository: $Repo_Name')</h4>"
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
		echo "<h3>$(gettext 'Private repositories')</h3>"
		[ -n "$(ls $LOCALSTATE/undigest 2> /dev/null)" ] && cat << EOT
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
		$(gettext 'Name') <input type="text" name="repository" size="10">
		$(gettext 'mirror')
		<input type="text" name="mirror" value="http://" size="50">
		<input type="submit" value="Add repository" />
	</p>
</form>

<h3>$(gettext 'Link to another SliTaz installation')</h3>

<p>$(gettext "This link points to the root of another SliTaz installation. \
You will be able to install packages using soft links to it.")</p>

<form method="get" action="$SCRIPT_NAME">
<p>
	<input type="hidden" name="admin" value="add-link" />
	<input type="text" name="link"
	 value="$(readlink $LOCALSTATE/fslink 2> /dev/null)" size="50">
	<input type="submit" name="admin" value="$(gettext 'Set link')" />
	<input type="submit" name="admin" value="$(gettext 'Remove link')" />
</p>
</form>
EOT
		version=$(cat /etc/slitaz-release)
		cat << EOT

<h3 id="dvd">$(gettext 'SliTaz packages DVD')</h3>

<p>$(eval_gettext "A bootable DVD image of all available packages for the \
\$version version is generated every day. It also contains a copy of the \
website and can be used without an internet connection. This image can be \
installed on a DVD or an USB key.")</p>

<div>
	<form method="post" action='$SCRIPT_NAME?admin&action=dvdimage#dvd'>
	<p>
		<a class="button"
			href='http://mirror.slitaz.org/iso/$version/packages-$version.iso'>
			<img src="$IMAGES/tazpkg.png" />$(gettext 'Download DVD image')</a>
		<a class="button" href='$SCRIPT_NAME?admin&action=dvdusbkey#dvd'>
			<img src="$IMAGES/tazpkg.png" />$(gettext 'Install from DVD/USB key')</a>
	</p>
	<div class="box">
		$(gettext 'Install from ISO image:')
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
			echo "$dev is installed on /mnt/packages"
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
				echo "$dev is installed on /mnt/packages"
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
<h2>$(gettext 'Summary')</h2>

<div id="actions">
	<a class="button" href="$SCRIPT_NAME?list">
		<img src="$IMAGES/tazpkg.png" />$(gettext 'My packages')</a>
EOT
		fslink=$(readlink $LOCALSTATE/fslink)
		[ -n "$fslink" -a -d "$fslink/$INSTALLED" ] &&
			cat << EOT
	<a class="button" href="$SCRIPT_NAME?linkable">
		<img src="$IMAGES/tazpkg.png" />$(gettext 'Linkable packages')</a>
EOT
		cat << EOT
	<a class="button" href="$SCRIPT_NAME?recharge">
		<img src="$IMAGES/recharge.png" />$(gettext 'Recharge list')</a>
	<a class="button" href="$SCRIPT_NAME?up">
		<img src="$IMAGES/update.png" />$(gettext 'Check upgrades')</a>
	<a class="button" href="$SCRIPT_NAME?admin">
		<img src="$IMAGES/edit.png" />$(gettext 'Administration')</a>
</div>

$(packages_summary)


<h3>$(gettext 'Latest log entries')</h3>

<pre>
`tail -n 5 /var/log/tazpkg.log | fgrep "-" | \
	awk '{print $1, $2, $3, $4, $5, $6, $7}'`
</pre>
EOT
		;;
esac

# xHTML 5 footer
xhtml_footer
exit 0
