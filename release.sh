#!/bin/bash

set -e  # Exit on error

# 1. Define the version file
VERSION_FILE="src/DependencySolver/_version.py"

# 2. Extract the version number from the file
if [[ -f "$VERSION_FILE" ]]; then
    NEW_VERSION="v$(grep -oP '(?<=__version__ = ")[^"]+' "$VERSION_FILE")"
    echo "📢 Detected version: $NEW_VERSION"
else
    echo "❌ Error: Version file $VERSION_FILE not found!"
    exit 1
fi

# 3. Commit and push the changes
git add CHANGELOG.md release_notes.md "${VERSION_FILE}"
git commit -m "Bump version to ${NEW_VERSION}"
git push origin main

# 4. Add and push the new tag
git tag "$NEW_VERSION"
git push origin "$NEW_VERSION"

echo "🚀 Released new version: $NEW_VERSION"
