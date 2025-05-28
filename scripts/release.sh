#!/bin/bash
set -e

# Check if version argument provided
if [ -z "$1" ]; then
  echo "Usage: ./scripts/release.sh [major|minor|patch]"
  exit 1
fi

# Bump version
echo "Bumping $1 version..."
bumpver update --$1

# Get new version
NEW_VERSION=$(bumpver show --no-fetch | grep -oP 'Current version: \K.*')

# Update changelog
echo "Updating changelog..."
git-cliff --unreleased --tag v$NEW_VERSION --output CHANGELOG.md

# Commit changes
git add pyproject.toml CHANGELOG.md src/__init__.py
git commit -m "Release v$NEW_VERSION"

# Create tag
git tag -a v$NEW_VERSION -m "Release v$NEW_VERSION"

# Push with tags
git push --follow-tags