#!/bin/bash
#
# packager.io before script
#

set -eux
uname -a
ruby -v
env

VERSION="$APP_PKG_VERSION-$APP_PKG_ITERATION"
echo "Setting VERSION information to $VERSION"
echo "$VERSION" > VERSION

# cleanup
script/build/cleanup.sh
