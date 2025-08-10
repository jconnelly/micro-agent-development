# Contributing to Micro-Agent Development Platform

Welcome! This guide will help you contribute effectively to the project while following our documentation and quality standards.

## 🚀 Quick Start

### 1. Set Up Git Hooks (Recommended)
```bash
# Install project git hooks for automatic validation
./.githooks/setup-hooks.sh
```

### 2. Understand the Documentation Rules
- **ANY code changes**: CLAUDE.md **ALWAYS REQUIRED** - must document all code changes for project tracking
- **Medium changes (11-50 lines)**: CHANGELOG.md recommended for user-facing changes
- **Major changes (>50 lines)**: CHANGELOG.md **required** + CLAUDE.md **required**

## 📋 Before Making Changes

### Check Existing Documentation
```bash
# Review current changelog
cat CHANGELOG.md

# Check recent commits for patterns
git log --oneline -10

# Review project rules
cat PROJECT_RULES.md
```

### Plan Your Changes
1. **Identify Impact**: Will this affect users or system behavior?
2. **Documentation Needs**: What docs need updating?
3. **Testing Requirements**: What testing is needed?
4. **Breaking Changes**: Will this break existing functionality?

## 🔄 Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feat/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Changes
- Write clear, maintainable code
- Add comments for complex logic
- Include docstrings for new Python functions/classes
- Follow existing code style and patterns

### 3. Update Documentation
Based on change size:

#### For ANY Code Changes (ALWAYS REQUIRED)
**CLAUDE.md MUST be updated** for all code changes:
```markdown
# Add to appropriate section in CLAUDE.md

## [Current Phase/Section]

### [Task/Feature Name] ✅ (if completed) or 🔄 (if in progress)

**Implementation Details**: Description of what was changed and why
- Technical implementation details
- Performance impact or improvements  
- Integration with existing systems
- Any breaking changes or considerations

**Impact Achieved**:
- ✅ Specific benefit 1
- ✅ Specific benefit 2
- ✅ System behavior changes
```

#### For Medium Changes (11-50 lines)
**CLAUDE.md** (required) + Consider updating CHANGELOG.md:
```markdown
## [Unreleased]

### Added
- Brief description of new functionality

### Changed  
- Description of what changed and why

### Fixed
- Bug fixes with brief description
```

#### For Major Changes (>50 lines)
**CLAUDE.md** (required) + **CHANGELOG.md REQUIRED** with detailed entries:
```markdown
## [Unreleased]

### Added
- Detailed description of new features
- Impact on users and system behavior
- Any new configuration options

### Changed
- Breaking changes and migration notes
- Performance improvements with metrics
- API changes with examples
```

#### Additional Documentation (when applicable)
1. **Update README.md** if usage changes
2. **Update API documentation** if applicable
3. **Update deployment guides** for infrastructure changes

### 4. Test Your Changes
```bash
# Run tests locally
python -m pytest tests/

# Test documentation builds (if applicable)
mkdocs serve

# Test deployment (if infrastructure changes)
docker-compose up --build
```

### 5. Commit Changes
The git hooks will automatically validate your commit:

```bash
# Standard commit (hooks will validate)
git add .
git commit -m "feat(api): add user authentication endpoint

Added JWT-based authentication with role-based access control.
Includes middleware for automatic token validation.

- JWT token generation and validation
- Role-based permission checking  
- Automatic token refresh handling

Closes #123"

# Skip hooks only for emergencies
git commit --no-verify -m "hotfix: critical production issue"
```

## 📝 Documentation Standards

### Commit Message Format
```
type(scope): brief description (≤50 chars)

Optional longer description explaining the what and why.
Wrap at 72 characters per line.

- Key change 1
- Key change 2  
- Key change 3

Closes #issue-number
Co-authored-by: Name <email@example.com>
```

### CHANGELOG.md Guidelines
- Keep entries under `## [Unreleased]` until release
- Use semantic versioning for releases (1.2.3)
- Group by `Added`, `Changed`, `Fixed`, `Removed`
- Focus on user impact, not implementation details
- Include migration notes for breaking changes

### CLAUDE.md Updates (Major Features)
For substantial features or phase completions:
- Document architectural changes
- Include business impact and technical benefits
- Provide implementation details and metrics
- Update phase tracking and completion status

## 🛡️ Quality Gates

### Pre-commit (Local)
- Documentation requirements validation
- CHANGELOG.md format checking
- Commit message validation
- Basic code quality checks

### CI/CD (GitHub Actions)
- Comprehensive documentation validation
- Test suite execution
- Code quality analysis
- Security scanning
- Build verification

### Pull Request Requirements
- [ ] CHANGELOG.md updated (if required)
- [ ] Tests pass
- [ ] Documentation is complete
- [ ] Code review completed
- [ ] No security issues
- [ ] Performance impact assessed

## 🔧 Troubleshooting

### Git Hook Issues
```bash
# Reinstall hooks
./.githooks/setup-hooks.sh

# Check hook permissions
ls -la .git/hooks/

# Fix permissions if needed
chmod +x .git/hooks/*
```

### Documentation Validation Failures
```bash
# Check CHANGELOG.md format
grep -n "# Changelog" CHANGELOG.md
grep -n "## \[Unreleased\]" CHANGELOG.md

# Validate against requirements
head -20 CHANGELOG.md
```

### Bypass for Emergencies
```bash
# Skip all hooks (use sparingly)
git commit --no-verify -m "emergency fix"

# Skip specific validation in CI
git push origin main --no-verify  # (admin only)
```

## 📊 Examples

### Small Change Example
```bash
# Fix typo in README
git commit -m "docs: fix typo in installation instructions"
# Hook: ✅ Passes (small change, no CHANGELOG required)
```

### Medium Change Example  
```bash
# Add new utility function
git add utils/helpers.py
git commit -m "feat(utils): add string formatting utilities

Added helper functions for consistent string formatting.
Includes validation and error handling.

- format_phone_number(): standardize phone formats
- format_currency(): currency formatting with locale support

Closes #456"
# Hook: ⚠️ Warns about CHANGELOG but allows commit
```

### Major Change Example
```bash
# Before committing major changes
echo "### Added
- New string formatting utilities with locale support
- Phone number and currency formatting functions
- Input validation and comprehensive error handling

### Impact
- Improves consistency across all user-facing text
- Reduces duplicate formatting code by 60%
- Supports internationalization for future expansion" >> CHANGELOG.md

git add utils/ CHANGELOG.md
git commit -m "feat(utils): add comprehensive formatting utilities

Complete rewrite of string formatting system with locale support.
Consolidates formatting logic and improves consistency.

- format_phone_number(): international format support
- format_currency(): locale-aware currency formatting  
- format_address(): standardized address formatting
- Comprehensive input validation and error handling
- 60% reduction in duplicate formatting code

Breaking Change: Old format_* functions moved to legacy module.
See CHANGELOG.md for migration guide.

Closes #456, #789"
# Hook: ✅ Passes (CHANGELOG updated, properly documented)
```

## 🆘 Getting Help

### Documentation Questions
- Review existing CHANGELOG.md entries for examples
- Check CLAUDE.md for major feature documentation patterns
- Use PROJECT_RULES.md for specific requirements
- Look at recent commits: `git log --oneline -20`

### Git Hook Problems
- Run `.githooks/setup-hooks.sh` to reinstall
- Check file permissions: `ls -la .git/hooks/`
- Test hooks manually: `.git/hooks/pre-commit`

### CI/CD Failures
- Check GitHub Actions logs for specific error messages
- Validate CHANGELOG.md format locally
- Ensure all required sections are present
- Test documentation builds locally if applicable

### When to Ask for Help
- Unsure about documentation requirements
- Complex architectural changes
- Breaking changes that affect multiple components
- Performance implications unclear
- Security considerations

## 🎯 Best Practices

### Documentation
- Write for your future self and team members
- Focus on **why** not just **what**
- Include examples for complex features
- Update docs **before** or **with** code changes, not after

### Code Quality
- Follow existing patterns and conventions
- Add tests for new functionality
- Consider performance implications
- Think about security from the start

### Collaboration  
- Ask questions early and often
- Share context in commit messages
- Review your own code before requesting review
- Be responsive to feedback

---

**Remember**: Good documentation is a gift to your future self and your team. These processes exist to maintain high quality and make everyone's life easier! 🚀✨