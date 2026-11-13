#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-only
# Publish the generated catalogue to its dedicated branch; source stays on dev.
set -euo pipefail
: "${GITHUB_TOKEN:?GitHub publication token is required}"
: "${GITHUB_REPOSITORY:?GitHub repository is required}"
: "${GITHUB_SHA:?Source commit is required}"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
python3 scripts/catalogue-bundle.py build . "$stage/bundle/v1" --commit "$GITHUB_SHA"
git -C "$stage" init -q -b published repository
git -C "$stage/repository" config user.name 'github-actions[bot]'
git -C "$stage/repository" config user.email '41898282+github-actions[bot]@users.noreply.github.com'
auth=$(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64 -w0)
git -C "$stage/repository" config http.https://github.com/.extraheader "AUTHORIZATION: basic $auth"
git -C "$stage/repository" remote add origin "https://github.com/$GITHUB_REPOSITORY.git"
if git -C "$stage/repository" ls-remote --exit-code origin refs/heads/published > /dev/null; then
    git -C "$stage/repository" fetch -q --depth=1 origin published
    git -C "$stage/repository" reset -q --hard FETCH_HEAD
else
    result=$?
    [[ $result == 2 ]] || exit "$result"
fi
rm -rf "$stage/repository/v1"
cp -R "$stage/bundle/v1" "$stage/repository/v1"
git -C "$stage/repository" add v1
if ! git -C "$stage/repository" diff --cached --quiet; then
    git -C "$stage/repository" commit -q -m "build: publish catalogue from $GITHUB_SHA"
    git -C "$stage/repository" push origin HEAD:published
fi
