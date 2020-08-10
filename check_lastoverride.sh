#!/usr/bin/env bash
#
#  Scans pages to identify those with an overrideLastMod tag that may be masking
#  newer commits.
#

HERE=$(dirname ${BASH_SOURCE[0]})
output=""

for i in $(find $HERE/content/pages -name \*.md -print0 | xargs -0 grep -i 'overridelastmod' -l)
do
    since_override=$(git log --pretty=oneline $i | egrep -v '(7a2d7187d39131bdd68e18749ce51fc0c767ecf1|8bd923e629251d4ece8fbaf7f79d5c56bf039b57|02c62644bd5e64c3442d9fe719ef4003d60b082c|642e537f01dc095047b1d77c6bd4f8dd5dcddcbb)' | wc -l | bc)

    # use below to generate some errors
    # since_override=$(git log --pretty=oneline $i | egrep -v '(7a2d7187d39131bdd68e18749ce51fc0c767ecf1|8bd923e629251d4ece8fbaf7f79d5c56bf039b57|02c62644bd5e64c3442d9fe719ef4003d60b082c)' | wc -l | bc)
    echo "Checking $i; $since_override unexpected modifications"
    if [[ $since_override != 0 ]]
    then
        output="$output\nWARNING: $i has overrideLastMod but has been changed recently"
    fi
done

if [ -z "$output" ]; then
    echo -e "\nNo spurious overrideLastMod tags found."
else
    echo -e $output >&2
fi
