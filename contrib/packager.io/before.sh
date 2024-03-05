#!/bin/bash
#
# packager.io before script
#

set -eu

VERSION="$APP_PKG_VERSION-$APP_PKG_ITERATION"
echo "Setting VERSION information to $VERSION"
echo "$VERSION" > VERSION

# The sha is the second element in APP_PKG_ITERATION
SHA=$(echo $APP_PKG_ITERATION | cut -d'.' -f2)

# Download info
echo "Getting info from github for commit $SHA"
curl -L \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/InvenTree/InvenTree/commits/$SHA > commit.json
curl -L \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/InvenTree/InvenTree/commits/$SHA/branches-where-head > branches.json

# Extract info
echo "Extracting info from github"
DATE=$(jq -r '.commit.committer.date' commit.json)
BRANCH=$(jq -r '.[].name' branches.json)
NODE_ID=$(jq -r '.node_id' commit.json)
SIGNATURE=$(jq -r '.commit.verification.signature' commit.json)

echo "Write VERSION information"
echo "INVENTREE_COMMIT_HASH='$SHA'" >> VERSION
echo "INVENTREE_COMMIT_DATE='$DATE'" >> VERSION
echo "INVENTREE_PKG_INSTALLER='PKG'" >> VERSION
echo "INVENTREE_PKG_BRANCH='$BRANCH'" >> VERSION
echo "INVENTREE_PKG_TARGET='$TARGET'" >> VERSION
echo "NODE_ID='$NODE_ID'" >> VERSION
echo "SIGNATURE='$SIGNATURE'" >> VERSION

echo "Written VERSION information"
cat VERSION
