#!/bin/bash

set -e  # Exit on error

# 1. Define the new version
NEW_VERSION="$1"  # Version is passed as a parameter (e.g., ./update_version_and_changelog.sh v1.2.3)
if [[ -z "$NEW_VERSION" ]]; then
    echo "❌ Error: Please provide the new version. Usage: ./update_version_and_changelog.sh v1.2.3"
    exit 1
fi

# 2. Update the version in _version.py file
VERSION_FILE="src/DependencySolver/_version.py"

if [[ -f "$VERSION_FILE" ]]; then
    # Replace the old version number with the new one
    sed -i "s/^__version__ = .*/__version__ = \"${NEW_VERSION#v}\"/" "$VERSION_FILE"
    echo "✅ Updated version in file: $VERSION_FILE"
else
    echo "❌ File $VERSION_FILE not found!"
    exit 1
fi

# 3. Generate the new CHANGELOG.md
echo "# [${NEW_VERSION}] - $(date +'%Y-%m-%d')" > new_changelog.md
echo "" >> new_changelog.md
cat release_notes.md >> new_changelog.md
echo "" >> new_changelog.md

# 4. Find the most recent previous tag (before the new version)
PREV_TAG=$(git tag -l "v*" | sort -V | tail -n 1)

if [[ -z "$PREV_TAG" ]]; then
    # If no previous tag exists, fallback to the first commit
    PREV_TAG=$(git rev-list --max-parents=0 HEAD)
fi

echo "### 🔄 Commit Changes Since Last Version ($PREV_TAG):" >> new_changelog.md
git log $PREV_TAG..HEAD --pretty=format:"- %s (%an)" >> new_changelog.md
echo "" >> new_changelog.md
echo "" >> new_changelog.md

# Check if CHANGELOG.md exists
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

# 5. Commit and push the changes (Uncomment and use if needed)
# git add CHANGELOG.md "$VERSION_FILE" release_notes.md
# git commit -m "Updated CHANGELOG and version $NEW_VERSION"
# git push origin main

# 6. Add the new tag and push it to GitHub (Uncomment and use if needed)
# git tag "$NEW_VERSION"
# git push origin "$NEW_VERSION"

# echo "🚀 Released new version: $NEW_VERSION"
