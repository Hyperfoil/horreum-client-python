# Release

This document aims to describe how to perform a release of the Horreum python library.

The versioning pattern should follow the [Horreum](https://github.com/Hyperfoil/Horreum) 
versioning scheme to keep coherence among all Horreum-related projects versions.

## Prerequisites

In order to perform the following release procedure correctly, certain prerequisites must be met:

- Installed `git`.
- Installed `poetry` python package, refer to the [doc](https://pypi.org/project/poetry/) for more details.
- Installed `yq` linux tool, refer to its [doc](https://github.com/mikefarah/yq).
- Enough privileges to push new branches in this repository.
- Enough privileges to push new commit in the `main` branch (note this is temporary requirement, 
in future direct pushes will be disallowed).

## Procedure

Note that releases (i.e., actual _git tags_) are performed from the corresponding _stable_ branch.

### Prepare the project for the next release cycle

This procedure should be executed from the `main` branch, thus, checkout that branch. 

```bash
git checkout main
```

Update the project for the next development cycle by running:

```bash
./scripts/next-dev-cycle.sh 
```

This will create the new _stable_ branch given the current development version.
E.g., if the current version is `0.14.dev`, it will create `0.14.x` _stable_ branch.

After that, it will update the current `main` branch by updating to the next development cycle.

You should see a new commit like `Next is <VERSION>` highlight the next release cycle.
This commit adds the newly created _stable_ branch to the CICD jobs, i.e., `ci.yaml` and `backport.yaml`.

To double-check the version, run:
```bash
poetry version
# horreum 0.15.dev
```

All changes have been performed locally, you now need to push those changes remotely:
```bash
# push main branch
git push origin main

# push newly created stable branch
STABLE_BRANCH=...
git push origin $STABLE_BRANCH
```

### Tag a new version

Checkout the _stable_ branch from which you want to tag a new release. 

```bash
STABLE_BRANCH=...
git checkout $STABLE_BRANCH
```

Update the version and create a git tag by running:
```bash
./scripts/update-version.sh -t -u
```

Where:
* `-t`, ensure the script creates a new tag.
* `-u`, update the HORREUM_BRANCH in the makefile.
* The scripts will output the new version, prefix it with `v` to obtain the tag.

Update to the next development version by running:
```bash
./scripts/update-version.sh -d
```
Where:
* `-d`, marks the version as development one.
* The scripts will output the new version.

Commit and push changes:

```bash
git commit -am "Next is <NEXT_DEV_VERSION>"

git push origin $STABLE_BRANCH

LATEST_TAG=...
git push origin $LATEST_TAG
```
