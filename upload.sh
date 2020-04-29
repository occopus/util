#!/bin/bash

set -ex

if [ ! -d wheelhouse ]; then
    echo -n 'Wheelhouse has not been generated yet. Run package.sh? [Y/n]'
    read
    if [ ! "$REPLY" || "$REPLY" == 'y' ]; then
        ./package.sh
    fi
fi

scp wheelhouse/OCCO?Util*.whl ubuntu@192.168.155.11:/opt/packages
