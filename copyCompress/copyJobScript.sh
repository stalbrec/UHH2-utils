#!/bin/bash -e

set -u

# Copy a file using gfal tools & check it's copied successfully
# Usage:
# ./copyJobSsript.sh <src file> <destination> <1 for force copy, 0 for error if destination already exists (default)>
#
# Both should *NOT* use the srm:// ... prefix

SRC="$1"
DEST="$2"
FORCE=0

if (( $# == 3 )); then
    FORCE="$3"
fi

# Do some checks
SRCBASENAME=$(basename "$SRC")

if [[ "$SRCBASENAME" != *.root ]]; then
    echo "source file should be *.root"
    exit 111
fi

if [[ $(basename "$DEST") != *.root ]]; then
    echo "destination file not stated explicitly, using source basename: $SRCBASENAME"
    DEST=$DEST/$SRCBASENAME
fi

# save copies with "local" paths (no prefix)
SRCLOCAL="$SRC"
DESTLOCAL="$DEST"

SRMPREFIX="srm://dcache-se-cms.desy.de:8443"

# add prefix that gfal-tools needs
if [[ "$SRC" == /pnfs/desy.de/cms/tier2/* ]]; then
    SRC="${SRMPREFIX}${SRC}"
fi

if [[ "$DEST" == /pnfs/desy.de/cms/tier2/* ]]; then
    DEST="${SRMPREFIX}${DEST}"
fi

echo "$SRC -> $DEST"
FORCEOPT=""
if (( $FORCE == 1 )); then
    FORCEOPT="-f"
fi
gfal-copy -pr --nbstreams=2 --timeout=28800 "$FORCEOPT" "$SRC" "$DEST"

# Now check we copied across successfully by counting number of events
# (using proper tree traversal, not Fast method)
numsrc=$(./countEvents "${SRCLOCAL}" 0)
numdest=$(./countEvents "${DESTLOCAL}" 0)
if (( $numsrc != $numdest )); then
    echo "Mismatch in # events: $numsrc vs $numdest"
    exit 12
fi
echo "Same # events: $numsrc"