#!/bin/bash

set -e  # Exit on error

# 1. Prompt the user for the new version number
read -p "Enter the new version (e.g., v1.2.3): " NEW_VERSION

# 2. Validate version format (vX.Y.Z where X, Y, and Z are numbers)
if [[ ! "$NEW_VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Invalid version format. Use the format vX.Y.Z (e.g., v1.2.3)."
    exit 1
fi

# 3. Update the version in _version.py file
VERSION_FILE="src/DependencySolver/_version.py"

if [[ -f "$VERSION_FILE" ]]; then
    # Replace the old version number with the new one
    sed -i "s/^__version__ = .*/__version__ = \"${NEW_VERSION#v}\"/" "$VERSION_FILE"
    echo "✅ Updated version in file: $VERSION_FILE"
else
    echo "❌ File $VERSION_FILE not found!"
    exit 1
fi

# 4. Generate the new CHANGELOG.md
echo "# [${NEW_VERSION}] - $(date +'%Y-%m-%d')" > new_changelog.md
echo "" >> new_changelog.md
cat release_notes.md >> new_changelog.md
echo "" >> new_changelog.md

# 5. Find the most recent previous tag (before the new version)
PREV_TAG=$(git tag -l "v*" | sort -V | tail -n 1)

if [[ -z "$PREV_TAG" ]]; then
    # If no previous tag exists, fallback to the first commit
    PREV_TAG=$(git rev-list --max-parents=0 HEAD)
fi

echo "### 🔄 Commit Changes Since Last Version ($PREV_TAG):" >> new_changelog.md
git log $PREV_TAG..HEAD --pretty=format:"- %s (%an)" >> new_changelog.md
echo "" >> new_changelog.md
echo "" >> new_changelog.md

# 6. Check if CHANGELOG.md exists
if [[ -f "CHANGELOG.md" ]]; then
    echo "✅ Found existing CHANGELOG.md, appending new content."

    # Append the current CHANGELOG content into the new changelog file
    cat CHANGELOG.md >> new_changelog.md
else
    echo "❌ ERROR: CHANGELOG.md not found. Aborting the update."
    exit 1
fi
mv new_changelog.md CHANGELOG.md

echo "✅ Updated CHANGELOG.md"
echo "Check that ${VERSION_FILE}, CHANGELOG.md and release_notes.md look OK"
echo "Then to make release run: ./release.sh 
