#!/bin/bash

set -ex

PDIR=env/packaging

DELOLDWHLDIR='no'
for arg in "$@"
do
  if [[ $arg == "--yes" ]]; then
    DELOLDWHLDIR='yes'
  fi
done

if [ -d wheelhouse ]; then
    if [ "$DELOLDWHLDIR" == 'yes' ]; then
        rm -rf wheelhouse
    else
        echo 'Delete old wheelhouse? [Y/n]'
        read
        if [ -z "$REPLY" ] || [ "$REPLY" == 'y' ]; then
            rm -rf wheelhouse
        fi
    fi
fi

rm -rf $PDIR
mkdir -p wheelhouse
virtualenv -p python3 $PDIR
source $PDIR/bin/activate
pip install --upgrade pip
pip install wheel
pip wheel . -w wheelhouse
deactivate
rm -rf $PDIR
