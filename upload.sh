#!/bin/bash

set -e

if [ ! -d wheelhouse ]; then
    echo -n 'Wheelhouse has not been generated yet. Run package.sh? [Y/n]'
    read
    if [ ! "$REPLY" || "$REPLY" == 'y' ]; then
        ./package.sh
    fi
fi

scp wheelhouse/OCCO?Util*.whl ubuntu@10.1.14.86:/tmp
ssh ubuntu@10.1.14.86 sudo cp /tmp/OCCO?Util*.whl /mnt/pypi/packages
