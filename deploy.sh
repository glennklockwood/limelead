#!/usr/bin/env bash
#
#  Script for cleaning up the mess that Hugo makes and deploying it
#
REPO_HOME="$(git rev-parse --show-toplevel)"

### The sed that ships with macOS doesn't work well
if which gsed >/dev/null; then
    SED=gsed
    echo "Using gsed instead of sed"
else
    SED=sed
fi

###
### The master recipe for building this website
###
function build_website {
    set -e

    check_clean_index
    check_required_binaries
    check_deploy_environment

    if [ -d "${REPO_HOME}/public" ]; then
        echo "Removing previous build"
        rm -rf "${REPO_HOME}/public/"
    fi

    echo "Recompiling html from markdown"
    hugo

    ### Fix the last update times since Hugo can't do this sensibly
    for md_file in $(find ${REPO_HOME}/content/ -type f -name \*.md); do
        fix_update_time "$md_file"
    done
    fix_update_time "GLOBAL"

    ### God only knows where the empty 404.html that Hugo generates is coming from.
    ### Replace it with the one I made.
    if [ -f "${REPO_HOME}/public/_404.html" ]; then
        mv "${REPO_HOME}/public/_404.html" "${REPO_HOME}/public/404.html"
    fi

    ### Clean up the duplicate x.html and x/index.html files that Hugo makes
    clean_redundant_htmls
    set +e
}

###
### The master recipe to deploy this website
###
function deploy_website {
    echo "Deploying html"
    rsync -avr "${REPO_HOME}/public/" "${WEBSITE_REMOTE_USER}@${WEBSITE_REMOTE_HOST}:${WEBSITE_REMOTE_PATH}/"
}

###
### Required settings to deploy website
###
function check_deploy_environment {
    if [ -z "$WEBSITE_REMOTE_USER" -o -z "$WEBSITE_REMOTE_HOST" -o -z "$WEBSITE_REMOTE_PATH" ]; then
        echo "You must have the following environment variables defined:"
        echo "    WEBSITE_REMOTE_USER (currently=$WEBSITE_REMOTE_USER)"
        echo "    WEBSITE_REMOTE_HOST (currently=$WEBSITE_REMOTE_HOST)"
        echo "    WEBSITE_REMOTE_PATH (currently=$WEBSITE_REMOTE_PATH)"
        exit 1
    fi
}

###
### Make sure pygmentize is installed.
### If it isn't available, html will silently come out all broken
###
function check_required_binaries {
    for required_bin in hugo pygmentize; do
        if ! which ${required_bin} >/dev/null 2>&1; then
            echo "${required_bin} was NOT found"
            exit 1
        fi
    done
}

###
### We rely on git commit logs to get the last-updated timestamps for each
### html file, so refuse to proceed unless our index is clean
###
function check_clean_index {
    if ! git diff-index --quiet --exit-code HEAD; then
        echo "It looks like the git index is not clean, so we cannot correctly" >&2
        echo "insert the 'Last modified' lines into our generated html.  Please" >&2
        echo "commit all changes and then re-run this script." >&2
        exit 1
    fi
}

###
### Update 'Last updated' times
###
function fix_update_time {
    declare -A months
    months=( [Jan]="January"    [Feb]="February"    [Mar]="March"
             [Apr]="April"      [May]="May"         [Jun]="June"
             [Jul]="July"       [Aug]="August"      [Sep]="September"
             [Oct]="October"    [Nov]="November"    [Dec]="December" )
    months=( [Jan]="1"  [Feb]="2"  [Mar]="3"  [Apr]="4"  [May]="5"  [Jun]="6"
             [Jul]="7"  [Aug]="8"  [Sep]="9"  [Oct]="10" [Nov]="11" [Dec]="12" )

    local md_file="$1"
    if [ "$md_file" == "GLOBAL" ]; then
        local html_file="${REPO_HOME}/public/index.html"
        local last_update="$(git log | grep -m1 '^Date:')"
    else
        local html_file="$($SED -e 's#'"${REPO_HOME}"'/content/#'"${REPO_HOME}"'/public/#' -e 's#\.md$#.html#' <<< "$md_file")"
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
    $SED -i 's#^ *Last modified.*$#Last modified '"$new_update"'#' $html_file
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


###
### Actually pull the trigger and run all of this
###
build_website
deploy_website
