#!/bin/bash
#
# packager.io before script
#

set -eu

REPO="InvenTree/InvenTree"
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
  https://api.github.com/repos/$REPO/commits/$SHA > commit.json
curl -L \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/$REPO/commits/$SHA/branches-where-head > branches.json
curl -L \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/$REPO/commits/$APP_PKG_VERSION > tag.json

# Extract info
echo "Extracting info from github"
DATE=$(jq -r '.commit.committer.date' commit.json)
BRANCH=$(jq -r '.[].name' branches.json)
NODE_ID=$(jq -r '.node_id' commit.json)
SIGNATURE=$(jq -r '.commit.verification.signature' commit.json)
FULL_SHA=$(jq -r '.sha' commit.json)

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

echo "ALL"
echo "##############"
printenv
echo "##############"

# Try to get frontend
# Check if tag sha is the same as the commit sha
TAG_SHA=$(jq -r '.sha' tag.json)
if [ "$TAG_SHA" != "$FULL_SHA" ]; then
  echo "Tag sha is not the same as commit sha"
  curl https://api.github.com/repos/$REPO/actions/runs?head_sha=$FULL_SHA > runs.json
  artifact_url=$(jq -r '.workflow_runs | .[] | select(.name=="QC").artifacts_url' runs.json)
  run_id=$(jq -r '.workflow_runs[] | select(.name=="QC").id' runs.json)
  curl $artifact_url > artifacts.json
  artifact_id=$(jq -r '.artifacts[] | select(.name=="frontend-build").id' artifacts.json)
  echo "Getting frontend from github via run artifact. Run id: $run_id, Artifact id: $artifact_id, Artifact url: $artifact_url"
  curl https://github.com/$REPO/actions/runs/$run_id/artifacts/$artifact_id -L
  ls
else
  echo "Getting frontend from github via tag"
  curl https://github.com/$REPO/releases/download/$APP_PKG_VERSION/frontend-build.zip -L frontend.zip
fi
unzip frontend.zip -d src/backend/InvenTree/web/static/web
echo "Unzipped frontend"
