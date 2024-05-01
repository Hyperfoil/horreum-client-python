#!/bin/bash

set -eo pipefail

# Default values
DEV_MODE=${DEV_MODE:=false}
MAIN_BRANCH=${MAIN_BRANCH:=main}
NEXT_VERSION=""

Help()
{
   # Display Help
   echo "This tool prepares the project to the next development cycle."
   echo ""
   echo "Syntax: next-dev-cycle [OPTIONS]"
   echo "options:"
   echo "h    Display this guide."
   echo ""
}

while getopts "hn::s" option; do
   case $option in
      h) Help
         exit;;
      *) ;;
   esac
done

if [ "$DEV_MODE" != "false" ]; then
  echo "WARNING: Dev mode enabled..."
fi

# Get current git branch
CURRENT_BRANCH=$(git symbolic-ref --short HEAD)
if [ "$CURRENT_BRANCH" != "$MAIN_BRANCH" ]; then
    echo "ERROR: Run the release process from $MAIN_BRANCH."
    exit 1
fi

echo "Preparing for next development cycle $CURRENT_BRANCH"

# Compute release version if not provided
if [ -z "$NEXT_VERSION" ]; then
    NEXT_VERSION=$(poetry version patch -s --dry-run)
fi

# Extract the major and minor version components
MAJOR_MINOR_VERSION=$(echo "$NEXT_VERSION" | awk -F. '{print $1 "." $2}')
# Compute stable branch from new version
STABLE_BRANCH="$MAJOR_MINOR_VERSION.x"

echo "Next version will be: $NEXT_VERSION"

echo "Creating stable branch $STABLE_BRANCH ..."
# Check if stable branch exists and create if necessary
if ! git rev-parse --verify "$STABLE_BRANCH" >/dev/null 2>&1; then
  echo "Creating and checkout stable branch $STABLE_BRANCH.."
  git checkout -b "$STABLE_BRANCH"
else
  echo "Stable branch $STABLE_BRANCH already existing"
  git checkout "$STABLE_BRANCH"
fi

echo "Updating $MAIN_BRANCH to the next development cycle ..."
git checkout "$MAIN_BRANCH"

# Update to the next patch to remove the .dev
UPDATE_VERSION_LOGS=$(./scripts/update-version.sh -n "patch")
# And then do minor release with dev
UPDATE_VERSION_LOGS=$(./scripts/update-version.sh -n "minor" -d)
NEXT_DEV_VERSION=$(echo "$UPDATE_VERSION_LOGS" | tail -n1)
NEXT_RELEASE_VERSION=$(poetry version patch -s --dry-run)

echo "Next release will be $NEXT_RELEASE_VERSION"
echo "Set next development version to $NEXT_DEV_VERSION"

# Update backport.yaml
sed -i "s/target-branch:.*/target-branch: $STABLE_BRANCH/" .github/workflows/backport.yaml

# Update ci.yaml
yq e -i ".on.push.branches += [\"$STABLE_BRANCH\"]" .github/workflows/ci.yaml

if [ "$DEV_MODE" != "true" ]; then
  git add .
  git commit -m "Next is $NEXT_RELEASE_VERSION"
fi
