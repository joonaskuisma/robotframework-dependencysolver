# [v1.2.1] - 2025-08-31

## 🚀 Release Notes

### 🐞 Bug Fixes
- 🛠 Fixed issue #8 where after adding GUI, DependencySolver does not work anymore without tkinter installed even without --ui option.

### 🔄 Commit Changes Since Last Version (v1.2.0):
- bugfix: Missing tkinter import on Linux (#8) (#9) (Joonas Kuisma)

# [v1.2.0] - 2025-06-03

## 🚀 Release Notes

### 🔥 What's New?
- ✨ Feature 1: --randomize option: Enables randomized test order. (#5)
- 🎉 Feature 2: --ui option: Launches a simple GUI (#6)

### 🔄 Commit Changes Since Last Version (v1.1.0):
- Add support for --randomize and --ui options (#7) (Joonas Kuisma)

# [v1.1.0] - 2025-03-06

## 🚀 Release Notes

### 🔥 What's New?
- Added support for older Robot Framework versions, starting from 5.0.

### 🐞 Bug Fixes
- Fixed a bug that prevents calling `path/your_test_suite.robot` suite directly.
- Fixed a bug that prevents using underscores `_` in Test Case names.

### 📈 Improvements
- Updated the CI workflow to include tests for multiple Robot Framework versions, improving test coverage and compatibility.
- Enhanced documentation to clarify supported versions and usage.

### 📦 Dependencies Updated
- Updated `robotframework` backward to v5.0+ from v7.0+ to support older versions.

### 🔄 Commit Changes Since Last Version (v1.0.0):
- Add Support for Older Robot Framework Versions (5.0+), Update CI & Improve Docs (#4) (Joonas Kuisma)

# [v1.0.0] - 2025-02-28

## 🚀 Release Notes

This is first Production/Stable release!

### 🔥 What's New?
- Added a feature to log the execution time of depsol

### 📈 Improvements
- Adjusted log levels for better clarity
- Cleaned up --help output formatting
- Refactored `run.py`
- Minor improvements to implementation

### ⚠️ Breaking Changes
- Small changes to how depsol is invoked and how commands are passed to Robot

### 🔄 Commit Changes Since Last Version (v0.3.2):
- build: Changed status from beta to production/stable (Joonas Kuisma)
- fix: trying to fix failing ci tests (Joonas Kuisma)
- ci: fix tests (Joonas Kuisma)
- test: Updated tests and reference logs (Joonas Kuisma)
- docs: Updated README (Joonas Kuisma)
- feat: Add execution time logging for depsol, adjust log levels, and improve --help output (Joonas Kuisma)
- ci: update_version_and_changelog fix (Joonas Kuisma)
- ci: update_version_and_changelog improvement (Joonas Kuisma)

# [v0.3.2] - 2025-02-20

## 🚀 Release Notes

### 🐞 Bug Fixes
- Fixed broken link in README.md
- Fixed --version output print

### 📈 Improvements
- Documentation updates
- Improvent CI and release process

### 🔄 Commit Changes Since Last Version (v0.3.1):
- ci: update_version_and_changelog typo fix (Joonas Kuisma)
- docs: Fix --version output print (Joonas Kuisma)
- ci: Update update_version_and_changelog script (Joonas Kuisma)
- docs: Update README.dev.md (Joonas Kuisma)
- ci: Update and add release scripts (Joonas Kuisma)
- ci: Update Github workflow and shell script (Joonas Kuisma)
- docs: Update release_notes_template (Joonas Kuisma)
- docs: Fix broken link in README (Joonas Kuisma)

## [v0.3.1] - 2025-02-18

### 📜 Official Release Notes

## 🚀 Release Notes – Version 0.3.1

### 📈 Improvements
- 🚀 Add automatic CHANGELOG and release_notes in CI.

### 🔄 Commit Changes Since Last Version (v0.3.0):
- docs: Update release notes (Joonas Kuisma)
- ci: Add script for update version and changelog (Joonas Kuisma)
- ci: CI fix: corrected release workflow (Joonas Kuisma)
- Bump version to 0.3.1 (Joonas Kuisma)
- docs: Update release_notes_template (Joonas Kuisma)
- ci: Update to final release_notes generating (Joonas Kuisma)
- ci: Add automatic CHANGELOG and final release notes (Joonas Kuisma)
- docs: Initial CHANGELOG and release_notes_template (Joonas Kuisma)

## [v0.3.0] - 2025-02-17

### 🔥 What's New?
- ✨ Feature: For `--pabot` option added new feature 'OPTIMIZED'

---