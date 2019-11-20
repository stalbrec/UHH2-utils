#!/bin/bash -e
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH_STORED
# printenv | sort
for arg
do
    # each arg is SRC:DEST
    # echo $arg
    src=${arg%:*}
    dest=${arg#*:}
    echo "$src -> $dest"
    ./copyJobScript.sh "$src" "$dest" 1
done