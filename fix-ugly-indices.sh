#!/bin/bash
#
#  --uglyUrls breaks the subdirectory indices; instead of making 
#    /subdir/index.html, it creates /subdir.html.  This script will have to
#    simply move /subdir.html to /subdir/index.html if
#      1. subdir/ and subdir.html both exist, and
#      2. subdir/index.html does not exist
# 

for dir in $(find $1 -type d); do
    if [ -f ${dir}.html ]; then
        if [ -f ${dir}/index.html ]; then
            echo "${dir} is a candidate but ${dir}/index.html already exists!" >&2
        else
            mv -v ${dir}.html ${dir}/index.html
        fi
    fi
done
