#!/bin/bash

set -eo pipefail

# Default values
DEV_MODE=${DEV_MODE:-false}
MAIN_BRANCH=${MAIN_BRANCH:-main}
NEXT_VERSION=""

Help()
{
   # Display Help
   echo "This tool prepares the project to the next development cycle."
   echo ""
   echo "Syntax: ${0} [OPTIONS]"
   echo "options:"
   echo "-h    Display this guide."
   echo ""
}

while getopts "h" option; do
   case $option in
      h) Help
         exit;;
      *) echo "Unrecognized option: ${OPTARG}"
         Help
         exit 1;;
   esac
done

if [ "$DEV_MODE" != "false" ]; then
  echo "WARNING: Dev mode enabled..."
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: You have uncommitted changes, exiting ..."
  exit 1
fi

echo "Preparing for next development cycle"

# Compute release version if not provided
if [ -z "$NEXT_VERSION" ]; then
    NEXT_VERSION=$(poetry version patch -s --dry-run)
fi

# Compute stable branch from next version
STABLE_BRANCH=$(sed -E -e 's/([^.]+\.[^.]+).*/\1.x/' <<< "$NEXT_VERSION")

echo "Next version will be: $NEXT_VERSION"

echo "Creating stable branch $STABLE_BRANCH ..."
# Check if stable branch exists and create if necessary
if ! git rev-parse --verify "$STABLE_BRANCH" >/dev/null 2>&1; then
  git branch "$STABLE_BRANCH" "$MAIN_BRANCH"
  echo "Stable branch $STABLE_BRANCH created"
else
  echo "Stable branch $STABLE_BRANCH already existing"
fi

echo "Updating $MAIN_BRANCH to the next development cycle ..."
git checkout "$MAIN_BRANCH"

# Update to the next patch to remove the .dev
./scripts/update-version.sh -n "patch" >/dev/null 2>&1
# And then do minor release with dev
NEXT_DEV_VERSION=$(./scripts/update-version.sh -n "minor" -d | tail -n1)
NEXT_RELEASE_VERSION=$(poetry version patch -s --dry-run)

echo "Next release will be $NEXT_RELEASE_VERSION"
echo "Set next development version to $NEXT_DEV_VERSION"

# Update backport.yaml
sed -i "s/target-branch:.*/target-branch: $STABLE_BRANCH/" .github/workflows/backport.yaml

# Update ci.yaml
yq e -i ".on.push.branches += [\"$STABLE_BRANCH\"]" .github/workflows/ci.yaml

if [ "$DEV_MODE" != "true" ]; then
  git commit -am "Next is $NEXT_RELEASE_VERSION"
fi
