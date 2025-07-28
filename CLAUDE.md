# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Memories

- Use gh instead of git for github actions and repository management

## Code Formatting and Testing

### Python Code Formatting
- **Black Version**: Always use `black==23.11.0` to match the version pinned in `requirements.txt`
- **isort Configuration**: Use `isort --profile black` for import sorting to maintain compatibility with Black
- **Installation**: Use `pipx install black==23.11.0` and `pipx install isort`
- **Commands for formatting**:
  ```bash
  # Format with specific black version
  ~/.local/bin/black src/
  
  # Sort imports with black profile  
  ~/.local/bin/isort --profile black src/
  
  # Check formatting (for CI compatibility)
  ~/.local/bin/black --check src/
  ~/.local/bin/isort --profile black --check-only src/
  ```

### Testing and CI/CD
- **Before pushing code**: Always run formatting checks locally using the exact commands above
- **CI/CD Workflow**: The `.github/workflows/ci-cd.yml` uses the same black version and isort profile
- **Docker Actions**: Use stable versions only:
  - `docker/login-action@v3`
  - `docker/setup-buildx-action@v3` 
  - `docker/metadata-action@v5`
  - `docker/build-push-action@v6`

## Development Workflow

### Branch Strategy
- **Primary Development**: All changes must be pushed to the `dev` branch
- **Main Branch**: Changes can only be made to `main` after approval on `dev`
- **Feature Branches**: Create feature branches from `dev`, merge back to `dev`

### Code Development Process
1. Create feature branch from `dev` branch
2. Make code changes
3. Run formatting: `~/.local/bin/black src/ && ~/.local/bin/isort --profile black src/`
4. Verify formatting: `~/.local/bin/black --check src/ && ~/.local/bin/isort --profile black --check-only src/`
5. Commit and push to feature branch
6. Create PR to `dev` branch
7. After approval, merge to `dev`
8. Monitor GitHub Actions for any CI/CD issues

## Project Management

### MVidarr Roadmap
- **Project Board**: https://github.com/users/prefect421/projects/1
- All development should be guided by the MVidarr Roadmap project board
- Issues should be prioritized and planned according to their position on the roadmap

### Issue Management
All issues should be planned with the following attributes:
- **Milestone**: Correlates to version number being released
- **Release Slot**: Designated release window for the issue
- **Start Date**: When work on the issue should begin
- **Stop Date**: Target completion date for the issue

### Release Management
- **Current Release**: Version 0.9.1
- **Versioning**: Milestones correlate directly to version numbers
- Releases are now utilized for version management and deployment