# Project Rules and Guidelines

This document outlines the rules and conventions that must be followed when contributing to the Micro-Agent Development Platform.

## 📋 Documentation Requirements

### Mandatory Documentation Updates

#### For All Commits:
- **Commit Messages**: Must be descriptive and follow conventional commit format when possible
- **Minimum Length**: 10 characters minimum for commit messages
- **No WIP Commits**: Avoid committing work-in-progress or temporary messages

#### For ANY Code Changes (any number of lines):
- **CLAUDE.md REQUIRED**: Must update CLAUDE.md for ALL code changes to track project progress
- **Documentation Required**: Add entry documenting what was changed and why
- **Progress Tracking**: Update relevant phase status or progress tracking
- **Technical Details**: Include technical implementation details
- **Impact Notes**: Note any impact on system behavior or performance

#### For Code Changes (>10 lines):
- **Consider CHANGELOG.md**: Update for user-facing changes
- **Docstrings**: New Python files should include proper docstrings
- **Comments**: Complex logic should be commented

#### For Major Changes (>50 lines):
- **CHANGELOG.md REQUIRED**: Must update CHANGELOG.md with user-facing details
- **CLAUDE.md REQUIRED**: Already required for all changes
- **README.md**: Consider updating if new features affect usage
- **Format**: Follow semantic versioning in changelog entries

### CHANGELOG.md Format Requirements

```markdown
# Changelog

## [Unreleased]

### Added
- New features and functionality

### Changed  
- Changes to existing functionality

### Fixed
- Bug fixes

### Removed
- Removed features

## [1.0.0] - 2024-MM-DD

### Added
- Initial release features
```

## 🔧 Git Hooks

### Automated Enforcement
The project includes git hooks that automatically enforce these rules:

#### Pre-commit Hook:
- Validates documentation requirements based on change size
- Checks CHANGELOG.md format if updated
- Provides interactive prompts for compliance
- Can be bypassed with `git commit --no-verify` if needed

#### Commit Message Hook:
- Validates commit message length and format
- Warns about non-conventional commit formats
- Blocks work-in-progress messages
- Checks for common formatting issues

### Setup Git Hooks

```bash
# Run the setup script to install hooks
./.githooks/setup-hooks.sh

# Or manually copy hooks
cp .githooks/* .git/hooks/
chmod +x .git/hooks/*
```

## 🚀 CI/CD Requirements

### GitHub Actions Validation
Pull requests automatically validate:
- Documentation completeness
- CHANGELOG.md format and requirements
- Code quality standards
- Test coverage

### Required PR Checks
- [ ] CHANGELOG.md updated for significant changes
- [ ] Documentation updated for new features
- [ ] Tests pass
- [ ] Code quality checks pass
- [ ] Security scans pass

## 📝 Commit Message Standards

### Recommended Format
```
type(scope): brief description

Optional longer description explaining the change.

- Key change 1
- Key change 2

Closes #issue-number
```

### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style/formatting
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `build`: Build system changes
- `phase[N]`: Major phase completions

### Examples
```bash
feat(api): add user authentication endpoint
fix(pii): resolve regex pattern matching issue
docs: update deployment guide with k8s instructions
phase12: complete Kubernetes deployment infrastructure
```

## 🔄 Development Workflow

### Before Committing
1. **Review Changes**: Self-review all code changes
2. **Run Tests**: Ensure all tests pass locally
3. **Update Documentation**: Update relevant documentation
4. **Check Requirements**: Verify documentation requirements are met
5. **Lint Code**: Run code formatting and linting tools

### For Major Features
1. **Plan Documentation**: Consider documentation needs upfront
2. **Update CLAUDE.md**: Document major architectural changes
3. **Comprehensive Testing**: Ensure thorough test coverage
4. **Performance Testing**: Validate performance impact
5. **Security Review**: Consider security implications

## 🛡️ Bypass Options

### Emergency Bypasses
Sometimes rules need to be bypassed for emergencies:

```bash
# Skip git hooks
git commit --no-verify -m "emergency fix"

# Skip CI checks (admin only)
git push origin main --no-verify
```

### When to Bypass
- **Critical Production Issues**: Hotfixes for production
- **Documentation-Only Changes**: Minor typo fixes
- **Automated Commits**: Bot or CI generated commits
- **Initial Setup**: First-time repository setup

### After Bypassing
- [ ] Create follow-up issue to address skipped requirements
- [ ] Update documentation within 24 hours
- [ ] Add proper changelog entries in next regular commit

## 📊 Metrics and Monitoring

### Documentation Health
The project tracks:
- Percentage of commits with documentation updates
- Changelog completeness and timeliness
- Documentation coverage for new features
- Response time to documentation issues

### Quality Gates
- **Pre-commit**: Local validation before commit
- **Pre-push**: Validation before pushing to remote
- **PR Checks**: Comprehensive validation on pull requests
- **Post-merge**: Additional validation after merging

## 🆘 Help and Support

### Getting Help
- **Git Hook Issues**: Check `.githooks/setup-hooks.sh` for troubleshooting
- **CI/CD Failures**: Review GitHub Actions logs for specific errors
- **Documentation Questions**: Refer to existing examples in CHANGELOG.md and CLAUDE.md
- **Format Questions**: Use the templates in `.github/PULL_REQUEST_TEMPLATE.md`

### Common Issues
1. **Hook Permission Issues**: Run `chmod +x .git/hooks/*`
2. **CI Documentation Failures**: Check CHANGELOG.md format requirements
3. **Large Commit Warnings**: Consider breaking into smaller commits
4. **Bypass Not Working**: Ensure you're using the correct `--no-verify` flag

## 🔄 Continuous Improvement

These rules are living guidelines that evolve with the project:
- **Feedback Welcome**: Suggest improvements via issues or PRs
- **Rule Updates**: Changes to rules require team discussion
- **Tool Improvements**: Enhance automation based on team needs
- **Process Refinement**: Regularly review and optimize workflows

---

**Remember**: These rules exist to maintain high-quality documentation and code standards. They're designed to help, not hinder development. When in doubt, err on the side of better documentation! 📚✨