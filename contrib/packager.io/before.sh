#!/bin/bash
#
# packager.io before script
#

set -eu

# The sha is the second element in APP_PKG_ITERATION
VERSION="$APP_PKG_VERSION-$APP_PKG_ITERATION"
SHA=$(echo $APP_PKG_ITERATION | cut -d'.' -f2)

# Download info
echo "INFO collection | Getting info from github for commit $SHA"
curl -L -s -f \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/$APP_REPO/commits/$SHA > commit.json
echo "INFO collection | Got commit.json with size $(wc -c commit.json)"
curl -L -s -f \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/$APP_REPO/commits/$SHA/branches-where-head > branches.json
echo "INFO collection | Got branches.json with size $(wc -c branches.json)"
curl -L -s -f \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/$APP_REPO/commits/$APP_PKG_VERSION > tag.json
echo "INFO collection | Got tag.json with size $(wc -c tag.json)"

# Extract info
echo "INFO extract | Extracting info from github"
DATE=$(jq -r '.commit.committer.date' commit.json)
BRANCH=$(jq -r '.[].name' branches.json)
NODE_ID=$(jq -r '.node_id' commit.json)
SIGNATURE=$(jq -r '.commit.verification.signature' commit.json)
FULL_SHA=$(jq -r '.sha' commit.json)

echo "INFO write | Write VERSION information"
echo "$VERSION" > VERSION
echo "INVENTREE_COMMIT_HASH='$SHA'" >> VERSION
echo "INVENTREE_COMMIT_SHA='$FULL_SHA'" >> VERSION
echo "INVENTREE_COMMIT_DATE='$DATE'" >> VERSION
echo "INVENTREE_PKG_INSTALLER='PKG'" >> VERSION
echo "INVENTREE_PKG_BRANCH='$BRANCH'" >> VERSION
echo "INVENTREE_PKG_TARGET='$TARGET'" >> VERSION
echo "NODE_ID='$NODE_ID'" >> VERSION
echo "SIGNATURE='$SIGNATURE'" >> VERSION

echo "INFO write | Written VERSION information"
echo "### VERSION ###"
cat VERSION
echo "### VERSION ###"

# Try to get frontend
echo "INFO frontend | Trying to get frontend"
# Check if tag sha is the same as the commit sha
TAG_SHA=$(jq -r '.sha' tag.json)
if [ "$TAG_SHA" != "$FULL_SHA" ]; then
  echo "INFO frontend | Tag sha '$TAG_SHA' is not the same as commit sha $FULL_SHA, can not download frontend"
else
  echo "INFO frontend | Getting frontend from github via tag"
  curl https://github.com/$APP_REPO/releases/download/$APP_PKG_VERSION/frontend-build.zip -L -O -f
  mkdir -p src/backend/InvenTree/web/static
  echo "INFO frontend | Unzipping frontend"
  unzip -qq frontend-build.zip -d src/backend/InvenTree/web/static/web
  echo "INFO frontend | Unzipped frontend"
fi
