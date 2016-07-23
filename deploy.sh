#!/bin/bash
#
#  Script for cleaning up the mess that Hugo makes and deploying it
#

### For converting last-modified times
declare -A months
months[Jan]="January"
months[Feb]="February"
months[Mar]="March"
months[Apr]="April"
months[May]="May"
months[Jun]="June"
months[Jul]="July"
months[Aug]="August"
months[Sep]="September"
months[Oct]="October"
months[Nov]="November"
months[Dec]="December"
months[Jan]="1"
months[Feb]="2"
months[Mar]="3"
months[Apr]="4"
months[May]="5"
months[Jun]="6"
months[Jul]="7"
months[Aug]="8"
months[Sep]="9"
months[Oct]="10"
months[Nov]="11"
months[Dec]="12"

###
### Figure out where the repo lives
###
REPO_HOME="$(git rev-parse --show-toplevel)"

###
### Required settings to deploy website
###
RSYNC_OPTIONS="-av"
if [ -z "$WEBSITE_REMOTE_USER" -o -z "$WEBSITE_REMOTE_HOST" -o -z "$WEBSITE_REMOTE_PATH" ]; then
    echo "You must have the following environment variables defined:"
    echo "WEBSITE_REMOTE_USER (currently=$WEBSITE_REMOTE_USER)"
    echo "WEBSITE_REMOTE_HOST (currently=$WEBSITE_REMOTE_HOST)"
    echo "WEBSITE_REMOTE_PATH (currently=$WEBSITE_REMOTE_PATH)"
    exit 1
fi

###
### Make sure pygmentize is installed.
### If it isn't available, html will silently come out all broken
###
if ! which pygmentize >/dev/null 2>&1; then
    echo "pygmentize was NOT found"
    exit 1
fi

###
### We rely on git commit logs to get the last-updated timestamps for each
### html file, so refuse to proceed unless our index is clean
###
if ! git diff-index --quiet --exit-code HEAD; then
    echo "It looks like the git index is not clean, so we cannot correctly" >&2
    echo "insert the 'Last modified' lines into our generated html.  Please" >&2
    echo "commit all changes and then re-run this script." >&2
    exit 1
fi

###
### Update 'Last updated' times
###
function fix_update_time {
    local md_file="$1"
    if [ "$md_file" == "GLOBAL" ]; then
        local html_file="${REPO_HOME}/public/index.html"
        local last_update="$(git log | grep -m1 '^Date:')"
    else
        local html_file="$(sed -e 's#'"${REPO_HOME}"'/content/#'"${REPO_HOME}"'/public/#' -e 's#\.md$#.html#' <<< "$md_file")"
        local last_update="$(git log "$md_file" | grep -m1 '^Date:')"
    fi
    if [ ! -f "$html_file" ]; then
        echo "Warning: $html_file not found (from $md_file)" >&2
        exit 1
    fi

    local month_abbr="$(awk '{print $3}' <<< $last_update)"
    local month="${months[$month_abbr]}"
    if [ -z "$month" ]; then
        month="$month_abbr"
    fi
#   local new_update=$(awk '{ printf( "%s %s, %s at %s\n", "'$month'", $4, $6, $5 )}' <<< "$last_update")
    local new_update=$(awk '{ printf( "%s/%s/%s at %s\n", "'$month'", $4, $6, $5 )}' <<< "$last_update")
    sed -i 's#^ *Last modified.*$#Last modified '"$new_update"'#' $html_file
    local ecode=$?
    if [ $ecode -eq 0 ]; then
        echo "Updated last modified time of $html_file to $new_update"
    else
        echo "Failed to update last modified time of $html_file"
    fi
}

###
### Hugo creates both x.html and x/index.html; deduplicate
###
function clean_redundant_htmls {
    for dir in $(find ${REPO_HOME}/public/ -type d); do
        if [ -f "${dir}.html" -a -f "${dir}/index.html" ]; then
            echo "Removing redundant ${dir}.html"
            rm "${dir}.html"
        fi
    done
}

set -e

if [ -d "${REPO_HOME}/public" ]; then
    echo "Removing previous build"
    rm -rf "${REPO_HOME}/public/"
fi

echo "Recompiling html from markdown"
hugo

for md_file in $(find ${REPO_HOME}/content/ -type f -name \*.md); do
    fix_update_time "$md_file"
done
fix_update_time "GLOBAL"

clean_redundant_htmls

echo "Deploying html"

set -x
rsync ${RSYNC_OPTIONS} -r "${REPO_HOME}/public/" "${WEBSITE_REMOTE_USER}@${WEBSITE_REMOTE_HOST}:${WEBSITE_REMOTE_PATH}/"
set +x
