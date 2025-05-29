#!/bin/bash
set -e

# Install required tools
pip install bumpver git-cliff

# Verify clean working directory
if [[ -n $(git status --porcelain) ]]; then
  echo "Working directory not clean. Commit changes first."
  exit 1
fi

# Run tests
pytest tests/

# Bump version interactively
PS3='Select version bump: '
options=("major" "minor" "patch" "Quit")
select opt in "${options[@]}"
do
  case $opt in
    "major"|"minor"|"patch")
      ./scripts/release.sh $opt
      break
      ;;
    "Quit")
      break
      ;;
    *) echo "Invalid option $REPLY";;
  esac
done