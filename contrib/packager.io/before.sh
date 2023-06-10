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

echo "Defining VERSION information"
HASH=$(git rev-parse --short HEAD)
DATE=$(git log -1 --format=%ci --date=format:%Y%m%d)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
PUBLISHER=$(git config --get remote.origin.url | sed -e 's/.*\///' -e 's/\.git//')

echo "Write VERSION information"
echo "INVENTREE_COMMIT_HASH='$HASH'" >> VERSION
echo "INVENTREE_COMMIT_DATE='$DATE'" >> VERSION
echo "INVENTREE_PKG_INSTALLER='PKG'" >> VERSION
echo "INVENTREE_PKG_BRANCH='$BRANCH'" >> VERSION
echo "INVENTREE_PKG_PUBLISHER='$PUBLISHER'" >> VERSION
echo "INVENTREE_PKG_PLATFORM='$TARGET'" >> VERSION

echo "Written VERSION information"
cat VERSION
