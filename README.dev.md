# Developer Guide

## Installation

Clone this repository by using command:

```cmd
git clone https://github.com/joonaskuisma/robotframework-dependencysolver.git
```

and then run:

```cmd
pip install -e .[dev]
```

Then you have editable development environment ready with pabot and pytest.

## Commit Message Guidelines (Conventional Commits)
To maintain a clear and structured commit history, we follow the **Conventional Commits** standard. 
Each commit message should be prefixed with a specific type that describes the change:

| Type      | Purpose                                              | Example |
|-----------|------------------------------------------------------|---------|
| feat      | Adds a new feature                                  | `feat: Add dark mode support` |
| fix       | Fixes a bug                                         | `fix: Resolve crash on login` |
| chore     | Updates tools or dependencies (no code changes)    | `chore: Update dependencies` |
| docs      | Documentation updates                              | `docs: Update README with API usage` |
| style     | Code formatting, no logic changes                  | `style: Format code with Black` |
| refactor  | Code restructuring without functional changes      | `refactor: Simplify authentication logic` |
| test      | Adds or updates tests                              | `test: Add unit tests for user service` |
| perf      | Performance improvements                          | `perf: Optimize image loading` |
| ci        | CI/CD configuration changes                       | `ci: Update GitHub Actions workflow` |
| build     | Changes to the build system or dependencies       | `build: Upgrade setuptools version` |

Remember to add ! if the commit change is not backward compatible.
For example: `feat!: Added new required parameters.` or use BREAKING CHANGE in commit message:

```
feat: Change authentication system

BREAKING CHANGE: User passwords are no longer stored, only OAuth2 tokens are used.
```

### Commenting Best Practices
- Use **descriptive comments** in the code to explain non-trivial logic.
- Prefer **inline comments** (`#`) for single lines.
- Use **docstrings** (`""" ... """`) for functions and modules.

## Pull Request (PR) Guidelines
1. Create a **feature branch** from `main`.
2. Use **Conventional Commits** for clear commit messages.
3. When submitting a PR:
   - Provide a **clear description** of the change.
   - Reference related **issues** using GitHub syntax:
     - `Fixes #123` (Closes the issue automatically when merged)
     - `Resolves #456` or `Addresses #789`
   - Request a review from at least **one team member**.
4. Ensure all tests pass before merging.
5. Use **draft PRs** for work-in-progress changes.

## Release Process
Releases are triggered by **tagging a commit** in Git. This can be done with scripts.

### How to Create a Release
1. Ensure all changes are merged into `main`.
2. Then write and save `release_notes.md`. Use `release_notes_template.md` format.
3. Run `./update_version_and_changelog.sh`
4. Check that `src/DependencySolver/_version.py`, `CHANGELOG.md` and `release_notes.md` look OK. Use git `git status` to check that only these three files are modified. 
5. Run `./release.sh`. This will make commit and add correct tag and then push them to GitHub.
6. Then the GitHub Actions workflow will:
   - Run tests.
   - Build and publish the package to **PyPI**.
   - Generate **automatic release notes**.
   - Verifies that latest package is in **PyPI**.

For any issues, create a **bug report** in GitHub Issues and reference the problematic version.

---
By following these guidelines, we ensure a smooth development workflow and maintain high-quality releases. 🚀
