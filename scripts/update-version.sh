#!/bin/bash

set -eo pipefail

DEV_MODE=${DEV_MODE:=false}

Help()
{
   # Display Help
   echo "Update the project version."
   echo ""
   echo "Syntax: update-version [OPTIONS]"
   echo ""
   echo "options:"
   echo "h    Display this guide."
   echo ""
   echo "n    Update the project to this version."
   echo "     The new version should ideally be a valid semver string or a valid bump rule:"
   echo "     patch, minor, major, prepatch, preminor, premajor, prerelease."
   echo "     Run 'poetry version --help' for more details."
   echo ""
   echo "d    The next version will be a development one."
   echo "     It will append '-dev' to the version."
   echo ""
   echo "t    Do git tag with the new version."
   echo ""
   echo "u    Update the HORREUM_BRANCH in the Makefile."
}

IS_DEVEL_VERSION=false
DO_TAG=false
DEVEL_VERSION_SUFFIX=".dev"
UPDATE_HORREUM_BRANCH=false

while getopts "hn:dtu" option; do
   case $option in
      h) Help
         exit;;
      n) NEW_VERSION=${OPTARG}
         ;;
      d) IS_DEVEL_VERSION=true
         ;;
      t) DO_TAG=true
         ;;
      u) UPDATE_HORREUM_BRANCH=true
         ;;
      *) ;;
   esac
done

if [ "$NEW_VERSION" = "" ]; then
  NEW_VERSION="patch"
fi

NEW_VERSION="$(poetry version $NEW_VERSION -s --dry-run)"

if [ "$IS_DEVEL_VERSION" = "true" ]; then
  NEW_VERSION="$NEW_VERSION$DEVEL_VERSION_SUFFIX"
fi

# Extract the major and minor version components
MAJOR_MINOR_VERSION=$(echo "$NEW_VERSION" | awk -F. '{print $1 "." $2}')
# Compute stable branch from new version
STABLE_BRANCH="$MAJOR_MINOR_VERSION.x"

# Update HORREUM_BRANCH on Makefile
if [ "$UPDATE_HORREUM_BRANCH" = "true" ]; then
  sed -i "s/HORREUM_BRANCH ?= \".*\"/HORREUM_BRANCH ?= \"$STABLE_BRANCH\"/" Makefile
fi

echo "Updating project version to $NEW_VERSION.."
poetry version "$NEW_VERSION" -v

# Generate raw client and run tests
make generate

if [ "$DO_TAG" = "true" ] && [[ ! "$NEW_VERSION" =~ "$DEVEL_VERSION_SUFFIX"$ ]]; then
  echo "Tagging version v$NEW_VERSION"
  if [ "$DEV_MODE" != "true" ]; then
    git add .
    git commit -m "Tagging version $NEW_VERSION"
    git tag "v$NEW_VERSION"
  fi
else
  echo "Skipping tag because disabled or development version"
fi

# Print the new version
echo "$NEW_VERSION"