#!/bin/bash

set -eo pipefail

DEV_MODE=${DEV_MODE:-false}

Help()
{
   # Display Help
   echo "Update the project version."
   echo ""
   echo "Syntax: ${0} [OPTIONS]"
   echo ""
   echo "options:"
   echo "-h               Display this guide."
   echo ""
   echo "-n NEW_VERSION   Update the project to this version."
   echo "                 The new version should ideally be a valid semver string or a valid bump rule:"
   echo "                 patch, minor, major, prepatch, preminor, premajor, prerelease."
   echo "                 Run 'poetry version --help' for more details."
   echo ""
   echo "-d               The next version will be a development one."
   echo "                 It will append '-dev' to the version."
   echo ""
   echo "-t               Do git tag with the new version."
   echo ""
   echo "-u               Update the HORREUM_BRANCH in the Makefile."
}

IS_DEVEL_VERSION=false
DO_TAG=false
DEVEL_VERSION_SUFFIX=".dev"
UPDATE_HORREUM_BRANCH=false
NEW_VERSION=${NEW_VERSION:-"patch"}

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
      *) echo "Unrecognized option: ${OPTARG}"
         Help
         exit 1;;
   esac
done

NEW_VERSION=$(poetry version "$NEW_VERSION" -s --dry-run)

if [ "$IS_DEVEL_VERSION" = "true" ]; then
  NEW_VERSION="$NEW_VERSION$DEVEL_VERSION_SUFFIX"
fi

# Compute stable branch from next version
STABLE_BRANCH=$(sed -E -e 's/([^.]+\.[^.]+).*/\1/' <<< "$NEW_VERSION")

# Update HORREUM_BRANCH on Makefile
if [ "$UPDATE_HORREUM_BRANCH" = "true" ]; then
  sed -i "s/HORREUM_BRANCH ?= \".*\"/HORREUM_BRANCH ?= \"$STABLE_BRANCH\"/" Makefile
fi

echo "Updating project version to $NEW_VERSION ..."
poetry version "$NEW_VERSION" -v

# Generate raw client
make generate

if [ "$DO_TAG" = "true" ] && [ "$IS_DEVEL_VERSION" = "false" ]; then
  echo "Tagging version v$NEW_VERSION"
  if [ "$DEV_MODE" != "true" ]; then
    git commit -am "Tagging version $NEW_VERSION"
    git tag "v$NEW_VERSION"
  fi
else
  echo "Skipping tag because disabled or this is a development version"
fi

# Print the new version
echo "$NEW_VERSION"
