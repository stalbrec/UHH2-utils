#!/usr/bin/env bash
#
# Remove missing files from XML using *missing*.txt files from datasetInfo.py
#
# Usage:
# ./cleanupXML.sh <dataset directory> <missing.txt> <missing_all.txt>

TOPDIR="$1"
echo "Looking for XML files in $TOPDIR"

XMLFILE=""

# First do XMLs where all are missing - much easier
while read line; do
    if [[ "$line" == *.xml ]]; then
        XMLFILE="$TOPDIR/$line"
        echo "Now deleting $XMLFILE"
        rm "$XMLFILE"
    fi
done < "$3"

# Now do all the other missing files
while read line; do
    # echo $line
    if [[ "$line" == *.xml ]]; then
        XMLFILE="$TOPDIR/$line"
        echo "Now processing $XMLFILE"
    elif [[ "$line" == "----------" ]]; then
        continue
    else
        if [[ -n "$XMLFILE" ]];then
            if [[ -f "$XMLFILE" ]]; then
                sed -i "\|$line|d" $XMLFILE
                # need the first backslash to escape and set | as delim
                # since / is already in $line
                # the |d means the whole line is deleted
            fi
        fi
    fi
done < "$2"
