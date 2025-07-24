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

### Development Workflow
1. Make code changes
2. Run formatting: `~/.local/bin/black src/ && ~/.local/bin/isort --profile black src/`
3. Verify formatting: `~/.local/bin/black --check src/ && ~/.local/bin/isort --profile black --check-only src/`
4. Commit and push
5. Monitor GitHub Actions for any CI/CD issues