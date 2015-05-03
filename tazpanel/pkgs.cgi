#!/bin/sh
#
# TazPkg CGI interface - Manage packages via a browser
#
# This CGI interface extensively uses tazpkg to manage packages and have
# its own code for some tasks. Please KISS, it is important and keep speed
# in mind. Thanks, Pankso.
#
# (C) 2011-2015 SliTaz GNU/Linux - BSD License
#

. lib/libtazpanel

. /etc/slitaz/slitaz.conf
. /etc/slitaz/tazpkg.conf

export TEXTDOMAIN='tazpkg'

get_config

_()  { local T="$1"; shift; printf "$(gettext "$T")" "$@"; echo; }
_n() { local T="$1"; shift; printf "$(gettext "$T")" "$@"; }
_p() {
	local S="$1" P="$2" N="$3"; shift 3;
	printf "$(ngettext "$S" "$P" "$N")" "$@"; }


#------
# menu
#------

case "$1" in
	menu)
		TEXTDOMAIN_original=$TEXTDOMAIN
		export TEXTDOMAIN='tazpkg'

		cat <<EOT
  <li tabindex="0">
   <span>$(gettext 'Packages')</span>
   <menu>
    <li><a data-icon="info" href="pkgs.cgi">$(gettext 'Summary')</a></li>
    <li><a data-icon="list"    href="pkgs.cgi?list&amp;my=my&amp;cat=all&amp;repo=Any">$(gettext 'My packages')</a></li>
    <li><a data-icon="refresh" href="pkgs.cgi?recharge" data-root>$(gettext 'Recharge list')</a></li>
    <li><a data-icon="upgrade" href="pkgs.cgi?up" data-root>$(gettext 'Check updates')</a></li>
    <li><a data-icon="admin"   href="pkgs.cgi?admin" data-root>$(gettext 'Administration')</a></li>
   </menu>
  </li>
EOT
		export TEXTDOMAIN=$TEXTDOMAIN_original
		exit
esac



#
# AJAX commands
#

case " $(GET) " in


	*\ filelist\ * )
		# Show installed files list
		pkg=$(GET pkg)
		cd $PKGS_DB

		header
		if [ -d $INSTALLED/$pkg ]; then
			files="$(wc -l < $INSTALLED/$pkg/files.list)"
			cat <<EOT
	<pre class="scroll">$(sort $INSTALLED/$pkg/files.list)</pre>
	<footer>$(_p '%s file' '%s files' $files $files)</footer>
EOT
		else
			cat <<EOT
	<pre class="scroll">$(lzcat files.list.lzma undigest/*/files.list.lzma \
		2>/dev/null | awk -vp="$pkg:" '$1==p{print $2}' | sort)</pre>
EOT
		fi
		exit 0 ;;


	*\ status\ * )
		# Show package status
		pkg=$(GET pkg)
		class='pkg'

		if grep -q "^$pkg"$'\t' $PKGS_DB/installed.info; then
			class='pkgi'
			grep -q "^$pkg$" $PKGS_DB/blocked-packages.list && class='pkgib'
		fi

		header
		echo -n "<a data-icon=\"$class\" href=\"?info=${pkg//+/%2B}\">$pkg</a>"
		exit 0 ;;


	*\ app_img\ * )
		# Show application image
		pkg=$(GET app_img)

		# check for icons defined with packages.icons file
		if [ -f "$PKGS_DB/packages.icons" ]; then
			predefined_icon="$(awk -F$'\t' -vpkg="$pkg" '{if ($1 == pkg) print $2}' $PKGS_DB/packages.icons)"
		fi
		predefined_icon="${predefined_icon:-package-x-generic}.png"

		current_user="$(who | cut -d' ' -f1)"
		if [ -n "$current_user" ]; then
			current_user_home="$(awk -F: -vu=$current_user '{if($1==u) print $6}' /etc/passwd)"
			current_icon_theme="$(grep gtk-icon-theme-name $current_user_home/.gtkrc-2.0 | cut -d'"' -f2)"
		fi
		current_icon_theme="/usr/share/icons/$current_icon_theme"

		# Preferred default icon is 48px package-x-generic
		default_pkg_icon="$(find -L $current_icon_theme -type f -path '*48*' -name $predefined_icon | head -n1)"
		# ... or package-x-generic with the bigger size
		if [ -z "$default_pkg_icon" ]; then
			default_pkg_icon="$(find -L $current_icon_theme -type f -name $predefined_icon | sort | tail -n1)"
		fi

		# Preferred package icon size is 48px
		pkg_icon="$(find -L $current_icon_theme -type f -path '*48*' -name "$pkg.png" | head -n1)"
		# ... or just bigger one
		if [ -z "$pkg_icon" ]; then
			pkg_icon="$(find -L $current_icon_theme -type f -name "$pkg.png" | sort | tail -n1)"
		fi
		# ... or one from pixmaps
		if [ -z "$pkg_icon" ]; then
			pkg_icon="$(find -L /usr/share/pixmaps -type f -name "$pkg.png" | head -n1)"
		fi

		header "Content-Type: image/png"
		cat "${pkg_icon:-$default_pkg_icon}"
		exit 0 ;;


	*\ show_receipt\ * )
		# Show package receipt
		pkg=$(GET show_receipt)
		if [ -d "$INSTALLED/$pkg" ]; then
			# Redirects to the receipt view
			header "HTTP/1.1 301 Moved Permanently" "Location: index.cgi?file=$INSTALLED/$pkg/receipt"
			exit 0
		else
			temp_receipt=$(mktemp -d)
			wget -O $temp_receipt/receipt -T 5 http://hg.slitaz.org/wok/raw-file/tip/$pkg/receipt
			if [ -e "$temp_receipt" ]; then
				# Redirects to the receipt view
				header "HTTP/1.1 301 Moved Permanently" "Location: index.cgi?file=$temp_receipt/receipt"
				exit 0
			else
				header; xhtml_header
				msg err "$(_ 'Receipt for package %s unavailable' $pkg)"
				xhtml_footer
				exit 0
			fi
		fi
		;;

esac


header


# xHTML 5 header with special side bar for categories.
TITLE=$(TEXTDOMAIN='tazpkg'; _ 'TazPanel - Packages')
xhtml_header | sed 's/id="content"/id="content-sidebar"/'


pkg_info_link() {
	echo "<a data-icon=\"$2\" href=\"?info=${1//+/%2B}\">$1</a>" | sed 's| data-icon=""||'
}


# Display localized short description

i18n_desc() {
	for L in $LANG ${LANG%%_*}; do
		if [ -e "$PKGS_DB/packages-desc.$L" ]; then
			LOCDESC=$(awk -F$'\t' -vp=$1 '{if ($1 == p) print $2}' $PKGS_DB/packages-desc.$L)
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
	cut -f 1,2,3 -d "|" | while read PACKAGE VERSION SHORT_DESC
	do
		class=pkg; [ -d $INSTALLED/${PACKAGE% } ] && class=pkgi
		i18n_desc $PACKAGE
		cat <<EOT
<tr>
	<td><input type="checkbox" name="pkg" value="$PACKAGE">$(pkg_info_link $PACKAGE $class)</td>
	<td>$VERSION</td>
	<td>$SHORT_DESC</td>
</tr>
EOT
	done
	unset IFS
}


parse_packages_info() {
	IFS=$'\t'
	while read PACKAGE VERSION CATEGORY SHORT_DESC WEB_SITE TAGS SIZES DEPENDS; do
		class='pkg'
		if grep -q "^$PACKAGE"$'\t' $PKGS_DB/installed.info; then
			class='pkgi'
			grep -q "^$PACKAGE$" $PKGS_DB/blocked-packages.list && class='pkgib'
		fi
		i18n_desc $PACKAGE
		cat <<EOT
<tr>
	<td><input type="checkbox" name="pkg" value="$PACKAGE">$(pkg_info_link $PACKAGE $class)</td>
	<td>$VERSION</td>
	<td>$SHORT_DESC</td>
</tr>
EOT
	done
	unset IFS
}


# Show button
show_button() {
	for button in $@; do
		class=''; misc=''
		case $button in
		recharge)     class='refresh'; label="$(_ 'Recharge list')"; misc=' data-root' ;;
		up)           class='upgrade'; label="$(_ 'Check upgrades')"; misc=' data-root' ;;
		list)         class='list';    label="$(_ 'My packages')" ;;
		tags)         class='tags';    label="$(_ 'Tags')" ;;
		linkable)     class='link';    label="$(_ 'Linkable packages')" ;;
		admin)        class='admin';   label="$(_ 'Administration')"; misc=' data-root' ;;
		*Install*nf*) class='install'; label="$(_ 'Install (Non Free)')" ;;
		*Install*)    class='install'; label="$(_ 'Install')" ;;
		*Remove*)     class='remove';  label="$(_ 'Remove')" ;;
		*Link*)       class='link';    label="$(_ 'Link')" ;;
		*Block*)      class='lock';    label="$(_ 'Block')" ;;
		*Unblock*)    class='unlock';  label="$(_ 'Unblock')" ;;
		*Chblock*)    class='chlock';  label="$(_ '(Un)block')" ;;
		*Repack*)     class='repack';  label="$(_ 'Repack')" ;;
		*saveconf*)   class='save';    label="$(_ 'Save configuration')" ;;
		*listconf*)   class='list';    label="$(_ 'List configuration files')" ;;
		*quickcheck*) class='check';   label="$(_ 'Quick check')" ;;
		*fullcheck*)  class='check';   label="$(_ 'Full check')" ;;
		*clean*)      class='remove';  label="$(_ 'Clean')" ;;
		*setlink*)    class='link';    label="$(_ 'Set link')" ;;
		*removelink*) class='unlink';  label="$(_ 'Remove link')" ;;
		*add-mirror)  class='add';     label="$(_n 'Add mirror')" ;;
		*add-repo)    class='add';     label="$(_n 'Add repository')" ;;
		toggle)       class='toggle';  label="$(_n 'Toggle all')" ;;
		esac
		if [ "$button" == 'toggle' ]; then
			echo -n "<span class=\"float-right\"><button data-icon=\"$class\" onclick=\"checkBoxes()\">$label</button></span>"
		else
			echo -n "<button data-icon=\"$class\" name=\"${button%%=*}\" value=\"${button#*=}\"$misc>$label</button>"
		fi
	done
}



#
# xHTML functions
#


# ENTER will search but user may search for a button, so put one.

search_form() {
	cat <<EOT
<form class="search"><!--
	--><a data-icon="web" href="http://pkg.slitaz.org/" target="_blank" title="$(_n 'Web search tool')"></a> <!--
	--><input type="search" name="search" results="5" autosave="pkgsearch" autocomplete="on"><!--
	--><button type="submit">$(_n 'Search')</button><!--
	--><button name="files" value="yes">$(_n 'Files')</button><!--
--></form>
EOT
}


table_head() {
	cat <<EOT
<table class="wide zebra pkglist" id="head1">
	<thead id="head2">
		<tr>
			<td>$(_ 'Name')</td>
			<td>$(_ 'Version')</td>
			<td>$(_ 'Description')</td>
		</tr>
	</thead>
	<tbody>
EOT
}


sidebar() {
	repo=$(COOKIE repo); repo=${repo:-Public}; [ -n "$(GET repo)" ] && repo=$(GET repo)
	  my=$(COOKIE my);     my=${my:-my};       [ -n "$(GET my)" ]   &&   my=$(GET my)
	 cat=$(COOKIE cat);   cat=${cat:-all};     [ -n "$(GET cat)" ]  &&  cat=$(GET cat)

	cat <<EOT
<script type="text/javascript">
function setCookie(name) {
	if (name=='cat') {
		var cats = document.getElementsByName('cat');
		for (var i = 0; i < cats.length; i++) {
			if (cats[i].checked) {
				document.cookie = name + "=" + cats[i].value;
				break;
			}
		}
	} else {
		document.cookie = name+"="+document.getElementById(name).value;
	}
}
function setValue(name, value) {
	document.getElementById(name).value=value;
	setCookie(name);
}
</script>
<form method="post" action="?list" style="position: absolute">

<div id="sidebar">
	<select id="my" value="$my" onchange="setCookie('my'); this.form.submit()">
		<option value="my">$(_ 'My packages')</option>
		<option value="no">$(_ 'All packages')</option>
	</select>
	<script type="text/javascript">setValue('my', "$my")</script>

	<h4>$(_ 'Categories')</h4>

	<div class="wide zebra">
		$(echo 'base-system x-window utilities network games graphics office
		multimedia development system-tools security misc meta non-free all
		extra' | tr ' ' '\n' | awk -vcat="$cat" -vn="1" '{
			system("gettext " $1 | getline tr)
			printf "<input type=\"radio\" name=\"cat\" id=\"c%s\" ", n
			printf "value=\"%s\"%s ", $1, $1==cat?" checked":""
			printf "onclick=\"setCookie(&#39;cat&#39;); this.form.submit()\">"
			printf "<label for=\"c%s\">%s</label>\n", n, tr
			n++
		}')
	</div>
EOT
#reminder; gettext 'all'; gettext 'extra'

	if [ -d $PKGS_DB/undigest ]; then
		cat <<EOT
	<h4>$(_ 'Repository')</h4>

	<select id="repo" onchange="setCookie('repo')">
		<option value="Public">$(_ 'Public')</option>
		$(for i in $(ls $PKGS_DB/undigest); do
			echo "<option value=\"$i\">$i</option>"
		done)
		<option value="Any">$(_ 'Any')</option>
	</select>
	<script type="text/javascript">setValue('repo', "$repo")</script>
EOT
	fi
	cat <<EOT
	<a data-icon="tags" href="?tags">$(_ 'All tags...')</a><br/>
	<a data-icon="list" href="?cats">$(_ 'All categories...')</a>
</div>
</form>
EOT
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


header_repo_name() {
	[ -d $PKGS_DB/undigest ] && [ "$repo" != "Public" ] && \
		_ 'Repository: %s' $(repo_name $1)
}


# Print links to the pages

pager() {
	PAGE_SIZE=${PAGE_SIZE:-100}
	[ "$PAGE_SIZE" != "0" ] && \
	awk -F'"' -vpage="$page" -vsize="$PAGE_SIZE" -vnum_lines="$(wc -l < $1)" -vtext="$(_ 'Pages:') " -vurl="?list&amp;page=" '
BEGIN{
	num_pages = int(num_lines / size) + (num_lines % size != 0)
	if (num_pages != 1) printf "<p>%s", text
}
{
	if (num_pages == 1) exit
	r = NR % size
	if (r == 1) {
		p = int(NR / size) + 1
		printf "<button class=\"pages%s\" name=\"page\" value=\"%s\" title=\"%s\n···\n", p==page?" current":"", p, $6
	} else if (r == 0)
		printf "%s\">%s</button> ", $6, int(NR / size)
}
END{
	if (num_pages == 1) exit
	if (r != 0) printf "%s\">%s</button>", $6, int(NR / size) + 1
	print "</p>"
}' $1
}


# Show packages list by category or tag

show_list() {
	PAGE_SIZE=${PAGE_SIZE:-100}
	page=$(GET page); page=${page:-1}
	cached=$(mktemp)
	[ -n "$tag" ] && cat=''
	{
		for L in $LANG ${LANG%%_*}; do
			if [ -e "$PKGS_DB/packages-desc.$L" ]; then
				sed '/^#/d' $PKGS_DB/packages-desc.$L; break
			fi
		done
		[ -e "$i/blocked-packages.list" ] && cat $i/blocked-packages.list
		sed 's|.*|&\ti|' $i/installed.info
		[ "$cat" == 'extra' ] || [ $1 == 'my' ] || cat $i/packages.info
		[ "$cat" == 'extra' ] &&
		sed 's,\([^|]*\)|*\([^|]*\).*,\1\t-\textra\t\2\thttp://mirror.slitaz.org/packages/get/\1\t-\t-\t-,' $PKGS_DB/extra.list
	} | sort -t$'\t' -k1,1 | sed '/^$/d' | awk -F$'\t' -vc="${cat:--}" -vt="${tag:--}" '
{
	if (PKG && PKG != $1) {
		if (SEL) {
			if (DSCL) DSC = DSCL
			printf "<tr><td><input type=\"checkbox\" name=\"pkg\" value=\"%s\" id=\"%s\">", PKG, PKG
			printf "<a data-icon=\"pkg%s%s\" href=\"?info=%s\">%s</a></td>", INS, BLK, gensub(/\+/, "%2B", "g", PKG), PKG
			printf "<td>%s</td><td>%s</td><td><a href=\"%s\"></a></td></tr>\n", VER, DSC, WEB
		}
		VER = DSC = WEB = DSCL = INS = BLK = SEL = ""
	}

	PKG = $1
	if (NF == 1) { BLK = "b"; next }
	if (NF == 2) { DSCL = $2; next }
	if (c == "all" || $3 == c || index(" "$6" ", " "t" ")) { SEL = 1 }
	if (SEL) {
		if ($9 == "i") { VER = $2; DSC = $4; WEB = $5; INS = "i"; next}
		if (! INS)     { VER = $2; DSC = $4; WEB = $5 }
	}
}' > $cached

	pager="$(pager $cached)"
	case $PAGE_SIZE in
		0) list="$(cat $cached)";;
		*) list="$(tail -n+$((($page-1)*$PAGE_SIZE+1)) $cached | head -n$PAGE_SIZE)";;
	esac

	if [ "$pager" != "<p>$(_ 'Pages:') </p>" ] && [ -n "${list:1:1}" ]; then
		cat <<EOT
<h3>$(header_repo_name $i)</h3>
$pager
	$(table_head)
		$list
	</tbody></table>
$pager
EOT
	fi
	rm -f $cached


	### Re-select packages when you return to the page

	# Find the packages list
	pkgs=$(echo "$QUERY_STRING&" | awk 'BEGIN{RS="&";FS="="}
		{if ($1=="pkg") printf "\"%s\", ", $2}')
	pkgs=$(httpd -d "${pkgs%, }")
	# now pkgs='"pkg1", "pkg2", ... "pkgn"'

	if [ -n "$pkgs" ]; then
		cat <<EOT
<script type="text/javascript">
var pkgs = [$pkgs];
var theForm = document.getElementById('pkglist');
for (index = 0; index < pkgs.length; index++) {
	if (document.getElementById(pkgs[index])) {
		// check existing
		document.getElementById(pkgs[index]).checked = 'true';
	}
	else {
		// add other as hidden
		var hInput = document.createElement('input');
		hInput.type = 'hidden';
		hInput.name = 'pkg';
		hInput.value = pkgs[index];
		theForm.appendChild(hInput);
	}
}
document.getElementById('countSelected').innerText = pkgs.length;
</script>
EOT
	fi
}


# Show links for "info" page

show_info_links() {
	if [ -n "$1" ]; then
		if [ "$3" == 'tag' ]; then icon='tag'; else icon='clock'; fi
		echo -n "<tr><td><b>$2</b></td><td>"
		echo $1 | tr ' ' $'\n' | awk -vt="$3" -vi="$icon" '{
			printf "<span><a data-icon=\"%s\" ", i;
			printf "href=\"?%s=%s\">%s</a></span>   ", t, gensub(/\+/, "%2B", "g", $1), $1
		}'
		echo "</td></tr>"
	fi
}



#
# Commands
#


case " $(GET) " in


	*\ linkable\ *)
		#
		# List linkable packages.
		#
		search_form; sidebar
		LOADING_MSG=$(_ 'Listing linkable packages...'); loading_msg

		cat <<EOT
<h2>$(_ 'Linkable packages')</h2>

<form class="wide">
	$(_ 'Selection:') $(show_button do=Link)
EOT
		table_head
		target=$(readlink $PKGS_DB/fslink)
		for pkg in $(ls $target/$INSTALLED); do
			[ -s $pkg/receipt ] && continue
			. $target/$INSTALLED/$pkg/receipt
			i18n_desc $pkg
			cat <<EOT
<tr>
	<td><input type="checkbox" name="pkg" value="$pkg" /><a data-icon="pkg" href="?info=${pkg//+/%2B}">$pkg</a></td>
	<td>$VERSION</td>
	<td>$SHORT_DESC</td>
	<td><a data-img="web" href="$WEB_SITE"></a></td>
</tr>
EOT
		done
		cat <<EOT
		</tbody>
	</table>
</form>
EOT
		;;


	*\ cats\ *)
		#
		# List of all categories.
		#
		search_form; sidebar

		echo "<h2>$(_ 'Categories list')</h2>"

		for pkgsinfo in $(repo_list /packages.info); do
			cat <<EOT
<section>
	<header>$(header_repo_name $(dirname $pkgsinfo))</header>
	<table class="wide zebra center">
		<thead>
			<tr>
				<td>$(_ 'Category')</td>
				<td>$(_ 'Available packages')</td>
				<td>$(_ 'Installed packages')</td>
			</tr>
		</thead>
		<tbody>
EOT
			{
				awk -F$'\t' '{print $3}' $pkgsinfo | sort | uniq -c
				awk -F$'\t' '{print $3}' $PKGS_DB/installed.info | sed 's|.*|& i|' | sort | uniq -c
			} | sort -k2,2 | awk '
			{
				c [$2] = "."
				if ($3) { i[$2] = $1; } else { m[$2] = $1; }
			}
			END {
				for (n in c) print n, m[n], i[n]
			}' | sort | awk '{
			printf "<tr><td><a href=\"?list&amp;cat=%s\">%s</a></td><td>%d</td><td>%d</td></tr>", $1, $1, $2, $3
			}'
			cat <<EOT
		</tbody>
	</table>
</section>
EOT
		done
		;;


	*\ list\ *|*\ page\ *)
		#
		# List all packages by category.
		#
		search_form; sidebar
		LOADING_MSG="$(_ 'Listing packages...')"; loading_msg

		bcat="<b>$cat</b>"; brepo="<b>$repo</b>"
		case $repo in
			Any)
				case $my in
					my) title="$(_ 'Installed packages of category "%s"' "$bcat")" ;;
					*)  title="$(_ 'All packages of category "%s"' "$bcat")" ;;
				esac ;;
			*)
				case $my in
					my) title="$(_ 'Installed packages of category "%s" in repository "%s"' "$bcat" "$brepo")" ;;
					*)  title="$(_ 'All packages of category "%s" in repository "%s"' "$bcat" "$brepo")" ;;
				esac ;;
		esac

		cat <<EOT
<h2>$(_ 'Packages list')</h2>
<p>$title</p>

EOT

		[ ! -f $PKGS_DB/packages.info ] && msg warn \
		"$(_ 'You can not view a list of all packages until recharging lists.')"

		[ "$REMOTE_USER" == "root" ] && cat <<EOT
<section>
	<div>$(_ 'Selected packages:') <span id="countSelected"></span></div>
	<footer>
		$({
			[ "$my" != 'my' ] && show_button do=Install
			show_button do=Chblock do=Remove
		} | sed 's|button |button form="pkglist" |g')
		$(show_button toggle)
	</footer>
</section>
EOT
		cat <<EOT

<form id="pkglist" class="wide">
EOT
		for i in $(repo_list ""); do
			show_list ${my#no}
		done
		cat <<EOT
</form>
<script type="text/javascript">window.onscroll = scrollHandler; setCountSelPkgs();</script>
EOT
		;;


	*\ search\ *)
		#
		# Search for packages. Here default is to search in packages.desc
		# and so get result including packages names and descriptions
		#
		pkg=$(GET search); [ -z "$pkg" ] && xhtml_footer && exit
		cd $PKGS_DB

		search_form | sed "s|name=\"search\"|& value=\"$pkg\"|"
		sidebar
		LOADING_MSG="$(_ 'Searching packages...')"; loading_msg

		cat <<EOT
<h2>$(_ 'Search packages')</h2>

<section>
	<div>$(_ 'Selected packages:') <span id="countSelected"></span></div>
	<footer>
		$(show_button do=Install do=Chblock do=Remove | sed 's|button |button form="pkglist" |g')
		$(show_button toggle)
	</footer>
</section>

<form id="pkglist" class="wide">
EOT
		if [ -n "$(GET files)" -o -n "$(echo $pkg | grep '/')" ]; then
			cat <<EOT
	<table class="wide zebra filelist">
	<thead>
		<tr>
			<td>$(_ 'Package')</td>
			<td>$(_ 'File')</td>
		</tr>
	<thead>
	<tbody>
EOT
			lzcat $(repo_list /files.list.lzma) | grep -Ei ": .*$(GET search)" | \
			while read PACKAGE FILE; do
				PACKAGE=${PACKAGE%:}
				class='pkg'
				if [ -d $INSTALLED/$PACKAGE ]; then
					class='pkgi'
					grep -q "^$PACKAGE$" $PKGS_DB/blocked-packages.list && class='pkgib'
				fi
				cat <<EOT
<tr>
	<td><input type="checkbox" name="pkg" value="$PACKAGE">$(pkg_info_link $PACKAGE $class)</td>
	<td>$(echo "$FILE" | sed "s|$pkg|<span class=\"diff-add\">&</span>|gI")</td>
</tr>
EOT
			done
		else
			table_head
			awk -F$'\t' 'BEGIN{IGNORECASE = 1}
			$1 " " $4 ~ /'$pkg'/{print $0}' $(repo_list /packages.info) | parse_packages_info
		fi
		cat <<EOT
	</tbody>
	</table>
</form>
<script type="text/javascript">window.onscroll = scrollHandler; setCountSelPkgs();</script>
EOT
		;;


	*\ recharge\ *)
		#
		# Lets recharge the packages list
		#
		search_form; sidebar
		LOADING_MSG="$(_ 'Recharging lists...')"; loading_msg

		cat <<EOT
<h2>$(_ 'Recharge')</h2>
<p>$(_ 'Recharge checks for new or updated packages')</p>

<section>
	<header>
		$(_ 'Recharging log')
		<form>$(show_button up)</form>
	</header>

	<pre class="scroll">
EOT
		echo $(_ 'Recharging packages list') | log
		tazpkg recharge | filter_taztools_msgs
		cat <<EOT
	</pre>

	<footer>$(_ 'Packages lists are up-to-date. You should check for upgrades now.')</footer>
</section>
EOT
		;;


	*\ up\ *)
		#
		# Upgrade packages
		#
		search_form; sidebar
		LOADING_MSG="$(_ 'Checking for upgrades...')"; loading_msg

		cat <<EOT
<h2>$(_ 'Up packages')</h2>

<section>
	<div>$(_ 'Selected packages:') <span id="countSelected"></span></div>
	<footer>
		$(show_button do=Install do=Chblock do=Remove | sed 's|button |button form="pkglist" |g')
		$(show_button toggle)
	</footer>
</section>

<form id="pkglist" class="wide">
EOT
		# Ask tazpkg to make "packages.up" file
		tazpkg up --check >/dev/null
		table_head

		for pkg in $(cat $PKGS_DB/packages.up); do
			grep -hs "^$pkg	" $PKGS_DB/packages.info $PKGS_DB/undigest/*/packages.info | parse_packages_info
		done

		cat <<EOT
		</tbody>
	</table>
</form>
<script type="text/javascript">window.onscroll = scrollHandler; setCountSelPkgs();</script>
EOT
		;;


	*\ do\ *)
		#
		# Do an action on one or some packages
		#
		search_form; sidebar
		loading_msg

		# Find the command
		cmd=$(echo $(GET do) | tr [:upper:] [:lower:])

		# Find the packages list
		pkgs=$(echo $QUERY_STRING | awk 'BEGIN{RS="&";FS="="}{if($1=="pkg")print $2}')
		pkgs=$(httpd -d "$pkgs")

		# Describe the command
		bpkgs="<b>$pkgs</b>"; opt=''
		case $cmd in
			install) MSG="$(_ 'Installing: %s'   "$bpkgs")"; opt='--forced'; cmd='get-install' ;;
			remove)  MSG="$(_ 'Removing: %s'     "$bpkgs")" ;;
			link)    MSG="$(_ 'Linking: %s'      "$bpkgs")"; opt="$(readlink $PKGS_DB/fslink)" ;;
			block)   MSG="$(_ 'Blocking: %s'     "$bpkgs")" ;;
			unblock) MSG="$(_ 'Unblocking: %s'   "$bpkgs")" ;;
			chblock) MSG="$(_ '(Un)blocking: %s' "$bpkgs")" ;;
			repack)  MSG="$(_ 'Repacking: %s'    "$bpkgs")" ;;
		esac

		cat <<EOT
<h2>TazPkg: $(GET do)</h2>

<div>$MSG</div>
EOT
		# Do the command for all asked packages
		cd /tmp
		export output='html'

		for pkg in $pkgs; do
			#echo $(_n 'y') | 
			tazpkg $cmd $pkg $opt 2>/dev/null | filter_taztools_msgs
		done
		;;


	*\ info\ *)
		#
		# Packages info
		#
		pkg=$(GET info)
		search_form; sidebar
		LOADING_MSG=$(_ 'Getting package info...'); loading_msg

		cat <<EOT
<section>
	<header>
		$(_ 'Package %s' $pkg)
		<form>
			<input type="hidden" name="pkg" value="${pkg#get-}"/>
EOT

		# Get receipt variables, show Install/Remove buttons
		if [ -d $INSTALLED/$pkg ]; then
			. $INSTALLED/$pkg/receipt
			files=$(wc -l < $INSTALLED/$pkg/files.list)
			[ "$REMOTE_USER" == "root" ] &&
			show_button do=Remove
		else
			cd $PKGS_DB
			eval "$(awk -F$'\t' -vp=$pkg '
			$1==p{
				printf "PACKAGE=\"%s\"; VERSION=\"%s\"; CATEGORY=\"%s\"; ", $1, $2, $3
				printf "SHORT_DESC=\"%s\"; WEB_SITE=\"%s\"; TAGS=\"%s\"; ", $4, $5, $6
				printf "SIZES=\"%s\"; DEPENDS=\"%s\"", $7, $8
			}' packages.info undigest/*/packages.info)"
			if [ -z "$PACKAGE" ]; then
				eval "$(awk -F'|' -vp=$pkg '
				$1==p{
					printf "PACKAGE=\"%s\"; SHORT_DESC=\"%s\"; WEB_SITE=\"%s\"; ", $1, $2, $3
					printf "CATEGORY=\"%s\"; VERSION=\"%s\"; LICENSE=\"%s\"; ", $4, $5, $6
				}' extra.list undigest/*/extra.list)"
				[ "$CATEGORY" ] || CATEGORY="non-free"
			fi
			PACKED_SIZE=${SIZES% *}
			UNPACKED_SIZE=${SIZES#* }
			[ "$REMOTE_USER" == "root" ] &&
			if [ "${pkg#get-}" != "$pkg" ]; then
				show_button "do=Install&amp;nf"
			else
				show_button do=Install
			fi
		fi

		# Show Block/Unblock, and Repack buttons
		[ "$REMOTE_USER" == "root" ] &&
		if [ -d $INSTALLED/$pkg ]; then
			if grep -qs "^$pkg$" $PKGS_DB/blocked-packages.list; then
				show_button do=Unblock
			else
				show_button do=Block
			fi
			show_button do=Repack
		fi

		# Translate short description
		i18n_desc $pkg

		# Show info table
		cat <<EOT
		</form>
	</header>

<table class="wide summary">
	<tr><td id="appImg"><img src="pkgs.cgi?app_img=$PACKAGE"/></td><td>
<table class="wide zebra summary" id="infoTable">
<tbody>
	<tr><td><b>$(_ 'Name')</b></td><td>$PACKAGE</td></tr>
	<tr><td><b>$(_ 'Version')</b></td><td>$VERSION</td></tr>
	<tr><td><b>$(_ 'Category')</b></td><td><a href="?list&amp;cat=$CATEGORY">$CATEGORY</a></td></tr>
	<tr><td><b>$(_ 'Description')</b></td><td>$SHORT_DESC</td></tr>
	$([ -n "$MAINTAINER" ] && echo "<tr><td><b>$(_ 'Maintainer')</b></td><td>$MAINTAINER</td></tr>")
	$([ -n "$LICENSE" ] && echo "<tr><td><b>$(_ 'License')</b></td><td><a href=\"?license=$pkg\">$LICENSE</a></td></tr>")
	<tr><td><b>$(_ 'Website')</b></td><td><a href="$WEB_SITE" target="_blank">$WEB_SITE</a></td></tr>
	$(show_info_links "$TAGS" "$(_ 'Tags')" 'tag')
	<tr><td><b>$(_ 'Sizes')</b></td><td>${PACKED_SIZE/.0/}/${UNPACKED_SIZE/.0/}</td></tr>
	$(show_info_links "$DEPENDS" "$(_ 'Depends')" 'info')
	$(show_info_links "$SUGGESTED" "$(_ 'Suggested')" 'info')
</tbody>
</table>
</td></tr></table>

	<footer>
		<a data-icon="text" href="?show_receipt=$pkg">$(_ 'View receipt')</a>
		<a data-icon="slitaz" href="?improve=$pkg">$(_ 'Improve package')</a>
	</footer>
</section>
<span id="ajaxStatus" style="display:none"></span>

<script type="text/javascript">
	var links = document.getElementById('infoTable').getElementsByTagName('a');
	for (var i = 0; i < links.length; i++) {
		console.log('i=%s, icon=%s.', i, links[i].dataset.icon);
		if (links[i].dataset.icon == 'clock') {
			links[i].parentNode.id = 'link' + i;
			pkg = links[i].innerText.replace(/\+/g, '%2B');
			ajax('pkgs.cgi?status&pkg=' + pkg, '1', 'link' + i);
		}
	}

</script>
EOT

		# Show description
		DESC="$(tazpkg desc $pkg)"
		[ -n "$DESC" ] && echo "<section><pre class="pre-wrap">$DESC</pre></section>"

		# Show configuration files list
		CONFIGS="$(tazpkg list-config $pkg | sed 's|\(.*\)|\1 \1|')"
		[ -n "$CONFIGS" ] && cat <<EOT
<section>
	<header>$(_ 'Configuration files')</header>
	<pre>$(printf '<a href="index.cgi?file=%s">%s</a>\n' $CONFIGS)</pre>
</section>
EOT

		# Show installed files list
		pkg=${pkg//+/%2B}
		cat <<EOT
<section>
	<header>$(_ 'Installed files')</header>
	<span id="fileList">
		<div style="text-align: center;"><span id="ajaxStatus"></span>$(_ 'Please wait')</div>
	</span>
</section>
<script type="text/javascript">ajax('pkgs.cgi?filelist&pkg=$pkg', '1', 'fileList');</script>
EOT
		;;


	*\ admin\ * )
		#
		# TazPkg configuration page
		#
		cmd=$(GET admin)
		pager="$(GET pager)"; pager=${pager:-$PAGE_SIZE}; pager=${pager:-100}
		mirror="$(GET mirror)"; mirror="${mirror%/}/"
		repository="$PKGS_DB/undigest/$(GET repository)"
		link="$(GET link)"; link=${link%/}
		search_form; sidebar
		loading_msg

		case "$cmd" in
			clean)
				rm -rf $CACHE_DIR/* ;;
			add-mirror)
				echo "$mirror" >> $(GET file) ;;
			rm-mirror)
				sed -i "/^"$(echo $mirror | sed 's|/|\\/|g')"$/d" $(GET file) ;;
			select-mirror)
				tazpkg setup-mirror "${mirror}packages/$(cat /etc/slitaz-release)/" | log ;;
			add-repo)
				mkdir -p $repository
				echo "$mirror" > $repository/mirror
				echo "$mirror" > $repository/mirrors ;;
			rm-repo)
				rm -rf $repository ;;
			setlink)
				[ -d "$link/$INSTALLED" ] && ln -fs $link $PKGS_DB/fslink ;;
			removelink)
				rm -f $PKGS_DB/fslink ;;
			pager)
				TP_CONF=/etc/slitaz/tazpanel.conf
				if [ -z "$PAGE_SIZE" ]; then
					echo -e "\n# Size of packages list page\nPAGE_SIZE=\"$pager\"" >> $TP_CONF
				else
					sed -i "s|PAGE_SIZE=.*|PAGE_SIZE=\"$pager\"|" $TP_CONF
				fi ;;
		esac

		cat <<EOT
<h2>$(_ 'Administration')</h2>

<p>$(_ 'TazPkg administration and settings')</p>

<form id="actions">
	<input type="hidden" name="admin"/>
	$(show_button action=saveconf action=listconf action=quickcheck action=fullcheck)
</form>
EOT
		case "$(GET action)" in
			saveconf)
				LOADING_MSG=$(_ 'Creating the package...'); loading_msg
				echo "<pre>"
				cd /tmp
				tazpkg repack-config | filter_taztools_msgs
				echo -n "$(_ 'Path:') "; ls /tmp/config-*.tazpkg
				echo "</pre>" ;;
			listconf)
				echo "<h4>$(_ 'Configuration files')</h4>"
				echo "<ul>"
				tazpkg list-config | while read file; do
					if [ -e $file ]; then
						echo "<li><a href=\"index.cgi?file=$file\">$file</a></li>"
					else
						echo "<li>$file</li>"
					fi
				done
				echo "</ul>" ;;
			quickcheck)
				LOADING_MSG=$(_ 'Checking packages consistency...'); loading_msg
				echo "<pre>"
				tazpkg check
				echo "</pre>" ;;
			fullcheck)
				LOADING_MSG=$(_ 'Full packages check...'); loading_msg
				echo "<pre>"
				tazpkg check --full
				echo "</pre>" ;;
			dvdimage)
				dev=$(POST dvdimage)
				mkdir -p /mnt/packages 2> /dev/null
				echo "<pre>"
				mount -t iso9660 -o loop,ro $dev /mnt/packages &&
				/mnt/packages/install.sh &&
				_ '%s is installed on /mnt/packages' $dev
				echo "</pre>" ;;
			dvdusbkey)
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
				done ;;
		esac

		cache_files=$(find $CACHE_DIR -name '*.tazpkg' | wc -l)
		cache_size=$(du -sh $CACHE_DIR | cut -f1 | sed 's|\.0||')
		[ "$cache_files" == 0 ] && cache_size="0K"
		mirror=$(cat $PKGS_DB/mirror)
		default_mirror=${mirror%/packages/*}
		cat <<EOT
<section>
	<header>$(_ 'Packages cache')</header>
	<form class="wide">
		<div>$(_ 'Packages in the cache: %s (%s)' $cache_files $cache_size)</div>
		<footer>$(show_button admin=clean)</footer>
	</form>
</section>


<section>
	<header>$(_ 'Current mirror list')</header>
EOT

		# List mirrors
		version=$(cat /etc/slitaz-release)
		for i in $PKGS_DB/mirrors $PKGS_DB/undigest/*/mirrors; do
			[ -s $i ] || continue
			if [ $i != $PKGS_DB/mirrors ]; then
				echo "<h4>$(_ 'Repository: %s' "$(repo_name $(dirname $i))")</h4>"
			fi
			cat <<EOT
	<form class="wide">
		<input type="hidden" name="admin" value="select-mirror"/>
		<table class="wide zebra">
EOT
			while read line; do
				cat <<EOT
			<tr>
				<td>
					<input type="radio" name="mirror" id="$line" value="$line" onchange="this.form.submit()"
					$([ "$line" == "$default_mirror/" ] && echo -n 'checked="checked"')>
					<label for="$line"><code>$line</code></label></td>
				<td><a data-img="web"    href="$line" target="_blank"></a></td>
				<td><a data-img="remove" href="?admin=rm-mirror&amp;mirror=$line&amp;file=$i" title="$(_ 'Delete')"></a></td>
			</tr>
EOT
			done < $i
			cat <<EOT
		</table>
	</form>

	<form class="wide">
		<footer>
			<input type="hidden" name="file" value="$i" />
			<input type="text" name="mirror" size="40" />
			$(show_button admin=add-mirror)
		</footer>
	</form>
EOT
		done
		cat <<EOT
</section>


<section>
	<header>$(_ 'Private repositories')</header>
EOT
		if [ -n "$(ls $PKGS_DB/undigest 2> /dev/null)" ]; then
			cat <<EOT
	<table class="wide zebra">
EOT
			ls $PKGS_DB/undigest 2> /dev/null | while read repo ; do
				cat <<EOT
		<tr>
			<td><code>$repo</code></td>
			<td><a data-img="remove" href="?admin=rm-repo&amp;repository=$repo" title="$(_ 'Delete')"></a></td>
		</tr>
EOT
			done
			cat <<EOT
	</table>
EOT
		fi

		cat <<EOT
	<form class="wide">
		<table>
			<tr><td>$(_ 'Name')</td><td><input type="text" name="repository" size="10"/></td></tr>
			<tr><td>$(_ 'URL:')</td><td><input type="text" name="mirror" value="http://"></td></tr>
		</table>
		<footer>
			$(show_button admin=add-repo)
		</footer>
	</form>
</section>


<section>
	<header>$(_ 'Link to another SliTaz installation')</header>
	<form class="wide">
		<div>
			$(_ "This link points to the root of another SliTaz installation. You will be able to install packages using soft links to it.")
		</div>
		<input type="text" name="link" value="$(readlink $PKGS_DB/fslink 2> /dev/null)"/>
		<footer>
			$(show_button admin=setlink admin=removelink)
		</footer>
	</form>
</section>


<section>
	<header id="dvd">$(_ 'SliTaz packages DVD')</header>

	<div>
		$(_ "A bootable DVD image of all available packages for the %s version is generated every day. It also contains a copy of the website and can be used without an internet connection. This image can be installed on a DVD or a USB key." $version)

		<form method="post" action='?admin&amp;action=dvdimage'>
			$(_ 'Install from ISO image:')
			<input type="text" name="dvdimage" size="40" value="/root/packages-$version.iso" />
		</form>
	</div>

	<footer>
		<button data-icon="download" onclick='http://mirror.slitaz.org/iso/$version/packages-$version.iso'>
			$(_ 'Download DVD image')</button>
		<button data-icon="link" onclick='?admin&amp;action=dvdusbkey'>
			$(_ 'Install from DVD/USB key')</button>
	</footer>
</section>


<section>
	<header>$(_ 'Packages list')</header>
	<form class="wide">
		<div>
			$(_ 'Long list of packages is paginated. Here you can set the page size (default: 100, turning off the pager: 0).')
		</div>
		<input type="hidden" name="admin" value="pager"/>
		<input type="number" name="pager" value="$pager" min="0" step="10" size="4"/>
		<footer>
			<button data-icon="ok" type="submit">$(_ 'Set')</button>
		</footer>
	</form>
</section>
EOT
		;;


	*\ license\ *)
		#
		# Show licenses for installed packages
		#
		search_form; sidebar

		pkg=$(GET license)
		case $pkg in
			/*)	[ -e $pkg ] && {
				echo "<h2>${pkg#/usr/share/licenses/}</h2>"
				case $pkg in
					*.htm*) cat $pkg ;;
					*)	echo "<pre style=\"white-space: pre-wrap\">"
						cat $pkg | htmlize | sed 's|\([hf]t*t*ps*://[a-zA-Z0-9./_-]*[a-zA-Z0-9/_-]\)|<a href="\1">\1</a>|'
						echo "</pre>"
						;;
				esac
				} ;;
			*)	echo "<h2>$(_ 'Licenses for package %s' $pkg)</h2>"
				OFFLINE=''
				if [ -e "$PKGS_DB/installed/$pkg" ]; then
					for lic in $(grep /usr/share/licenses/ $PKGS_DB/installed/$pkg/files.list); do
						OFFLINE="$OFFLINE	<li><a href=\"?license=$lic\">licenses/<b>${lic#/usr/share/licenses/}</b></a></li>\n"
					done
					echo "\
Apache|Apache-2.0||||http://www.apache.org/licenses/#Artistic|Artistic-2.0||||#\
BSD|BSD-2-Clause||||#BSD3|BSD-3-Clause||||#CC-BY-SA||by-sa/4.0/|||#\
CC-SA||by-sa/4.0/|||#CC-BY-ND||by-nd/4.0/|||#CC-BY-NC-SA||by-nc-sa/4.0/|||#\
CC-BY-NC-ND||by-nc-nd/4.0/|||#CC-BY-NC||by-nc/4.0/|||#CC-BY||by/4.0/|||#\
cc-pd|||||http://creativecommons.org/publicdomain/#CDDL|CDDL-1.0||||#\
CECILL|CECILL-2.1||||#Eclipse|EPL-1.0||||#EPL|EPL-1.0||||#FDL|||fdl||#\
GPL|gpl-license||gpl|gpl.txt|#GPL2|GPL-2.0||old-licenses/gpl-2.0||#\
GPL3|GPL-3.0||gpl|gpl.txt|#ISC|ISC||||#LGPL|lgpl-license||lgpl||#\
LGPL2|||old-licenses/lgpl-2.0||#\
LGPL2.1|LGPL-2.1||old-licenses/lgpl-2.1|lgpl.txt|#LGPL3|LGPL-3.0||lgpl||#\
LPPL|LPPL-1.3c||||#MIT|MIT|||mit.txt|#MPL|MPL-2.0|||mozilla.txt|#\
MPL2|MPL-2.0||||#PublicDomain|||||http://creativecommons.org/publicdomain/#\
QPL|QPL-1.0||||#SIL_OFL|OFL-1.1||||#OFL|OFL-1.1||||#zlib/libpng|Zlib||||" | \
awk -vlicenses="$(. $PKGS_DB/installed/$pkg/receipt; echo "$LICENSE")" \
					-vtext="$(_ '%s license on %s website' %s %s)" \
					-vro="$(_ 'Read online:')" -vrl="$(_ 'Read local:')" \
					-vofflic="$OFFLINE" '
BEGIN{ FS="|"; RS="#"; split(licenses, lic, " "); if (offlic) OFFLINE[0]=offlic }
function link1(u, l, ll, w) {
	return sprintf("\t<li><a href=\"%s%s\">" text "</a></li>", u, l, "<b>" ll "</b>", w) }
function link2(u, l, ll) {
	return sprintf("\t<li><a href=\"%s%s\">%s</b></a></li>", u, l, ll) }
function link_osl(n) {
	return link1("http://opensource.org/licenses/", n, n, "OSL") }
function link_cc(n) {
	split(n, ll, "/")
	return link1("http://creativecommons.org/licenses/", n, ll[1], "Creative Commons") }
function link_gnu(n) {
	split(n, ll, "/")
	return link1("https://www.gnu.org/licenses/", n ".html", ll[2] ? ll[2] : ll[1], "GNU") }
function link_loc(n) {
	return link2("?license=/usr/share/licenses/", n, "licenses/<b>" n "</b>") }
function link_url(n) {
	return link2(n, "", n) }
{
	if ($1 == lic[1] || $1 == lic[2] || $1 == lic[3] || $1 == lic[4]) {
		if ($2) ONLINE[$2]=link_osl($2)
		if ($3) ONLINE[$3]=link_cc($3)
		if ($4) ONLINE[$4]=link_gnu($4)
		if ($5) OFFLINE[$5]=link_loc($5)
		if ($6) OFFLINE[$6]=link_url($6)
	}
}
END{
	if (length(ONLINE)  > 0) { print "<p>" ro "</p>\n<ul>"; for (o in ONLINE)  print ONLINE[o]; print "</ul>"  }
	if (length(OFFLINE) > 0) { print "<p>" rl "</p>\n<ul>"; for (o in OFFLINE) print OFFLINE[o]; print "</ul>" }
}'
				fi ;;
		esac
		;;


	*\ tags\ *)
		#
		# Show tag cloud
		#
		search_form; sidebar

		echo "<h2>$(_ 'Tags list')</h2>"
		brepo="<b>$repo</b>"
		case $repo in
			Any) title="$(_ 'List of tags in all repositories')" ;;
			*)   title="$(_ 'List of tags in repository "%s"' "$brepo")" ;;
		esac
		echo "<p>$title</p><p id=\"tags\">"
		to_read=""
		for i in $(repo_list ""); do
			if [ ! -e $i/packages.info ]; then
				list=installed
			else
				list=packages
			fi
			to_read="$to_read $i/$list.info"
		done
		TAGS="$(awk -F$'\t' '{if($6){print $6}}' $to_read | tr ' ' $'\n' | sort | uniq -c)"
		MAX="$(echo "$TAGS" | awk '{if ($1 > MAX) MAX = $1} END{print MAX}')"
		echo "$TAGS" | awk -vMAX="$MAX" '{
			printf "<a class=\"tag%s\" href=\"?tag=%s\" title=\"%s\">%s</a> ", int($1 * 7 / MAX + 1), $2, $1, $2
		}'
		echo "</p>"
		;;


	*\ tag\ *)
		#
		# Show packages with matching tag
		#
		search_form; sidebar

		tag=$(GET tag)
		cat <<EOT
<h2 data-icon="tag">$(_ 'Tag "%s"' $tag)</h2>
EOT
		[ "$REMOTE_USER" == "root" ] && cat <<EOT
<section>
	<div>$(_ 'Selected packages:') <span id="countSelected"></span></div>
	<footer>
		$(show_button do=Install do=Chblock do=Remove | sed 's|button |button form="pkglist" |g')
		$(show_button toggle)
	</footer>
</section>
EOT
		cat <<EOT
<form id="pkglist" class="wide">
EOT
		for i in $(repo_list ""); do
			show_list all
		done
		cat <<EOT
</form>
<script type="text/javascript">window.onscroll = scrollHandler; setCountSelPkgs();</script>
EOT
		;;


	*\ blocked\ *)
		#
		# Show blocked packages list
		#
		search_form; sidebar

		cat <<EOT
<h2>$(_ 'Blocked packages list')</h2>

<section>
	<div>$(_ 'Selected packages:') <span id="countSelected"></span></div>
	<footer>
		$(show_button do=Unblock | sed 's|button |button form="pkglist" |g')
		$(show_button toggle)
	</footer>
</section>

<form id="pkglist" class="wide">
EOT
		table_head
		for i in $(cat $PKGS_DB/blocked-packages.list); do
			awk -F$'\t' -vp="$i" '{
			if ($1 == p)
				printf "<tr><td><input type=\"checkbox\" name=\"pkg\" value=\"%s\"><a data-icon=\"pkgib\" href=\"?info=%s\">%s</a></td><td>%s</td><td>%s</td><td><a href=\"%s\"></a></td></tr>\n", $1, gensub(/\+/, "%2B", "g", $1), $1, $2, $4, $5
			}' $PKGS_DB/installed.info
		done
		cat <<EOT
		</tbody>
	</table>
</form>
<script type="text/javascript">window.onscroll = scrollHandler; setCountSelPkgs();</script>
EOT
		;;


	*\ improve\ *)
		#
		# Improving packages by the community effort
		#
		search_form; sidebar
		msg warn 'Under construction!<br/>It is only imitation of working'

		pkg=$(GET improve)
		user=$(POST user); type=$(POST type); text="$(POST text)"
		login=$(POST login); password=$(POST password)

		login_c=$(COOKIE login); password_c=$(COOKIE password)
		mail_hash=$(COOKIE mail_hash); user_name=$(COOKIE user_name)

		n=$'\n'

		if [ -n "$login" ]; then
			# Get mail hash and user Name from bugs.slitaz.org
			page="$(busybox wget --post-data "auth=${login}&pass=${password}&id=" \
				-O- "http://bugs.slitaz.org/bugs.cgi?user=${login}")"
			# Parse page and get:
			mail_hash="$(echo "$page" | fgrep '<h2>' | cut -d/ -f5 | cut -c 1-32)"
			user_name="$(echo "$page" | fgrep '<h2>' | cut -d'>' -f3 | cut -d'<' -f1)"

			# Put variables to the session Cookies (they clean in browser close)
			cat <<EOT
<script type="text/javascript">
	document.cookie = "login=$login";
	document.cookie = "password=$password";
	document.cookie = "mail_hash=$mail_hash";
	document.cookie = "user_name=$user_name";
</script>
EOT
			login_c="$login"; password_c="$password"
		fi

		if [ -z "$login_c" ]; then
			cat <<EOT
<section>
	<div>$(_ 'Please log in using your TazBug account.')</div>
	<form method="post">
		<input type="hidden" name="improve" value="$pkg"/>
		<table>
			<tr><td>$(_ 'Login:')</td>
				<td><input type="text" name="login"/></td></tr>
			<tr><td>$(_ 'Password:')</td>
				<td><input type="password" name="password"/></td></tr>
			<tr><td colspan="2">
				<button type="submit" data-icon="user">$(_ 'Log in')</button></td></tr>
		</table>
	</form>
	<footer>
		<a href="http://bugs.slitaz.org/bugs.cgi?signup&online" target="_blank">$(_ 'Create new account')</a>
	</footer>
</section>
EOT
			xhtml_footer; exit 0
		fi


		# Get receipt variables, show Install/Remove buttons
		if [ -d $INSTALLED/$pkg ]; then
			. $INSTALLED/$pkg/receipt
		else
			cd $PKGS_DB
			eval "$(awk -F$'\t' -vp=$pkg '
			$1==p{
				printf "VERSION=\"%s\"; SHORT_DESC=\"%s\"; TAGS=\"%s\"; ", $2, $4, $6
			}' packages.info undigest/*/packages.info)"
		fi

		RECEIPT="$(wget -O - http://hg.slitaz.org/wok/raw-file/tip/$pkg/receipt | htmlize)"
		DESCRIPTION="$(wget -O - http://hg.slitaz.org/wok/raw-file/tip/$pkg/description.txt | htmlize)"
		DESCRIPTION="$(separator)$n${DESCRIPTION:-(empty)}$n$(separator)"

		if [ -z "$type" ]; then
			cat <<EOT
<section>
	<header>
		$(_ 'Improve package "%s"' $pkg)
		<form><button name="info" value="$pkg" data-icon="back">$(_ 'Back')</button></form>
	</header>

	<div style="display:none">
		<span id="newVersion">Current version: $VERSION${n}New version: $VERSION${n}Link to announce: http://</span>
		<span id="improveShortDesc">Short description (English):$n$SHORT_DESC</span>
		<span id="translateShortDesc">Short description (English):$n$SHORT_DESC$n${n}Language: $LANG${n}Short description:$n$SHORT_DESC</span>
		<span id="improveDesc">Description (English):$n$DESCRIPTION</span>
		<span id="translateDesc">Language: $LANG${n}Description:$n$DESCRIPTION</span>
		<span id="improveCategory">Old category: $CATEGORY${n}New category: $CATEGORY</span>
		<span id="improveTags">Tags: $TAGS</span>
		<span id="addIcon">Link to application icon (48x48px): http://</span>
		<span id="addScreenshot">Link to application screenshot: http://</span>
		<span id="improveReceipt">$RECEIPT</span>
		<span id="improveOther"></span>
	</div>

	<form method="post" class="wide">

		<table class="wide">
			<tr><td style="vertical-align:bottom">
				<input type="hidden" name="improve" value="$pkg"/>
				<input type="hidden" name="user" value="$login_c"/>
				&nbsp;$(_ 'How can you help:')<br/>
				<select name='type' id="improveType" onchange="improveAction()">
					<option value=''>$(_ 'Please select an action')
					<option value='newVersion'>$(_ 'Report new version')
					<option value='improveShortDesc'>$(_ 'Improve short description')
					<option value='translateShortDesc'>$(_ 'Translate short description')
					<option value='improveDesc'>$(_ 'Add or improve description')
					<option value='translateDesc'>$(_ 'Translate description')
					<option value='improveCategory'>$(_ 'Improve category')
					<option value='improveTags'>$(_ 'Add or improve tags')
					<option value='addIcon'>$(_ 'Add application icon')
					<option value='addScreenshot'>$(_ 'Add application screenshot')
					<option value='improveReceipt'>$(_ 'Improve receipt')
					<option value='improveOther'>$(_ 'Other')
				</select>
			</td>
			<td id="user_info">$user_name
				<img src="http://www.gravatar.com/avatar/$mail_hash?s=48&amp;d=identicon"
					style="border-radius: 0.3rem"/>
			</td></tr>
		</table>

		<textarea name="text" id="improveText" style="width:100%; resize: vertical; min-height:10rem"></textarea>
		<button type="submit" data-icon="slitaz">$(_ 'Send')</button>
	</form>
</section>
EOT
		else
			cat <<EOT
<section>
	<header>
		$(_ 'Thank you!')
		<form><button name="info" value="$pkg" data-icon="back">$(_ 'Back')</button></form>
	</header>
<div>The following information was sent to SliTaz developers:</div>
<pre class="scroll"><b>User:</b> $user
<b>Type:</b> $type
<b>Package:</b> $pkg
<b>Message:</b>
$(echo "$text" | htmlize)</pre>
</section>
EOT
		fi
		;;


	*)
		#
		# Default to summary
		#
		search_form; sidebar

		cat <<EOT
<form id="actions2">
EOT
		fslink=$(readlink $PKGS_DB/fslink)
		[ -n "$fslink" -a -d "$fslink/$INSTALLED" ] && show_button linkable
		show_button recharge up admin
		cat <<EOT
</form>

<section>
	<header>$(_ 'Summary')</header>

	<table class="wide zebra">
		<tr>
			<td>$(_ 'Last recharge:')</td>
			<td>$(list=$PKGS_DB/ID
	if [ -e $list ]; then
		# Timezone offset as string, ex. '+0200' for EET (+2 hours)
		ohhmm="$(date +%z)"
		# Timezone offset in the seconds
		offset=$(( 60 * (60 * ${ohhmm:0:3} + ${ohhmm:3:2}) ))
		daynow=$(( ($(date          +%s) + $offset) / 86400 ))
		dayupd=$(( ($(date -r $list +%s) + $offset) / 86400 ))
		days=$(( $daynow - $dayupd ))
		time=$(date -r $list +%R)
		ago="$(_p '%d day ago.' '%d days ago.' $days $days)"
		case $days in
			0) _ 'Today at %s.' $time;;
			1) _ 'Yesterday at %s.' $time;;
			[2-9]) echo $ago;;
			*) echo "<span style='color:red'>$ago</span>"
				_ 'It is recommended to [recharge] the lists.' | \
				sed 's|\[|<a data-icon="refresh" href="?recharge">|;s|\]|</a>|';;
		esac
	else
		_ 'never.'
		_ 'You need to [download] the lists for further work.' | \
		sed 's|\[|<a data-icon="download" href="?recharge" data-root>|;s|\]|</a>|'
	fi)</td></tr>
		<tr>
			<td>$(_ 'Installed packages:')</td>
			<td><a href="?list&amp;my=my&amp;cat=all&amp;repo=Any">
				<b>$(cat $PKGS_DB/installed.info | wc -l)</b>
				</a></td></tr>
		<tr>
			<td>$(_ 'Mirrored packages:')</td>
			<td><a href="?list&amp;my=no&amp;cat=all&amp;repo=Any">
				<b>$(cat $PKGS_DB/packages.list | wc -l)</b>
				</a></td></tr>
		<tr>
			<td>$(_ 'Upgradeable packages:')</td>
			<td><a href="?up">
				<b>$(cat $PKGS_DB/packages.up | wc -l)</b>
				</a></td></tr>
		<tr>
			<td>$(_ 'Installed files:')</td>
			<td><b>$(cat $INSTALLED/*/files.list | wc -l)</b></td></tr>
		<tr>
			<td>$(_ 'Blocked packages:')</td>
			<td><a href="?blocked">
				<b>$(cat $PKGS_DB/blocked-packages.list | wc -l)</b>
				</a></td></tr>
	</table>
</section>


<section>
	<header>
		$(_ 'Latest log entries')
		<form action="index.cgi">
			<button name="file" value="$LOG" data-icon="view">$(_ 'Show')</button>
		</form>
	</header>
	<pre>$(tail -n 5 $LOG | tac | fgrep "-" | awk '{print $1, $2, $3, $4, $5, "<a href=\"?info=" $6 "\">" $6 "</a>", $7}')</pre>
</section>
EOT
		;;
esac

# xHTML 5 footer
export TEXTDOMAIN='tazpkg'
xhtml_footer
exit 0
