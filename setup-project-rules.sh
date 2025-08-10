#!/bin/bash

# Setup Project Rules and Documentation Standards
# This script configures git hooks and project standards for consistent documentation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║              Micro-Agent Project Rules Setup                    ║"
    echo "║                                                                  ║"
    echo "║  This script configures automatic documentation enforcement      ║"
    echo "║  and project quality standards for consistent development        ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header

print_info "Starting project rules setup..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository. Please run this from the project root."
    exit 1
fi

print_success "Git repository detected"

# Setup git hooks
print_info "Installing git hooks for documentation enforcement..."

if [ -f ".githooks/setup-hooks.sh" ]; then
    bash .githooks/setup-hooks.sh
    print_success "Git hooks installed successfully"
else
    print_warning "Git hooks setup script not found. Manual installation may be required."
fi

# Validate CHANGELOG.md exists and has proper format
print_info "Validating CHANGELOG.md..."

if [ ! -f "CHANGELOG.md" ]; then
    print_warning "CHANGELOG.md not found. Creating basic template..."
    cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to the Micro-Agent Development Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup

### Changed

### Fixed

### Removed

EOF
    print_success "CHANGELOG.md created with proper template"
else
    # Validate existing CHANGELOG.md
    if grep -q "# Changelog" CHANGELOG.md && grep -q "## \[Unreleased\]" CHANGELOG.md; then
        print_success "CHANGELOG.md format validation passed"
    else
        print_warning "CHANGELOG.md exists but may not follow the required format"
        print_info "Please ensure it contains '# Changelog' header and '## [Unreleased]' section"
    fi
fi

# Check if GitHub workflows directory exists
print_info "Checking GitHub Actions configuration..."

if [ -d ".github/workflows" ]; then
    print_success "GitHub Actions directory found"
    if [ -f ".github/workflows/documentation-check.yml" ]; then
        print_success "Documentation check workflow configured"
    else
        print_warning "Documentation check workflow not found"
    fi
else
    print_info "GitHub Actions not configured (this is optional for local development)"
fi

# Verify PROJECT_RULES.md exists
if [ -f "PROJECT_RULES.md" ]; then
    print_success "PROJECT_RULES.md documentation found"
else
    print_warning "PROJECT_RULES.md not found. Consider creating it for team reference."
fi

# Check for contributing guidelines
if [ -f "docs/CONTRIBUTING.md" ] || [ -f "CONTRIBUTING.md" ]; then
    print_success "Contributing guidelines found"
else
    print_info "Consider adding CONTRIBUTING.md for new contributors"
fi

# Test git hooks by creating a test commit (dry run)
print_info "Testing git hook installation..."

# Create a temporary test file
echo "# Test file for git hooks" > test_hook_validation.tmp

# Try to add and check what would happen
git add test_hook_validation.tmp > /dev/null 2>&1 || true

# Check if hooks are executable
if [ -x ".git/hooks/pre-commit" ] && [ -x ".git/hooks/commit-msg" ]; then
    print_success "Git hooks are properly installed and executable"
else
    print_warning "Git hooks may not be properly installed. Run .githooks/setup-hooks.sh manually"
fi

# Clean up test file
git reset HEAD test_hook_validation.tmp > /dev/null 2>&1 || true
rm -f test_hook_validation.tmp

print_info "Setup complete! Here's what was configured:"
echo ""
echo "📋 Documentation Standards:"
echo "   • Git hooks enforce CLAUDE.md updates for ALL code changes (any size)"
echo "   • Git hooks enforce CHANGELOG.md updates for major changes (>50 lines)"  
echo "   • Commit message validation for quality and format"
echo "   • Automatic format checking for CHANGELOG.md updates"
echo ""
echo "🔧 Available Commands:"
echo "   • git commit                    # Normal commit with validation"
echo "   • git commit --no-verify        # Skip validation (emergencies only)"
echo "   • .githooks/setup-hooks.sh      # Reinstall git hooks"
echo ""
echo "📝 Documentation Files:"
echo "   • CHANGELOG.md                  # Project changelog (required updates)"
echo "   • PROJECT_RULES.md              # Complete project rules reference"
echo "   • docs/CONTRIBUTING.md          # Contributor guidelines"
echo "   • .github/PULL_REQUEST_TEMPLATE.md # PR template with checklist"
echo ""

if command -v code > /dev/null 2>&1; then
    print_info "VS Code detected. The project includes .vscode/settings.json with:"
    echo "   • Git commit message templates"
    echo "   • Markdown formatting rules"
    echo "   • Documentation highlighting"
fi

echo ""
print_success "🎉 Project rules setup complete!"
print_info "Next steps:"
echo "   1. Read PROJECT_RULES.md to understand ALL code changes require CLAUDE.md updates"
echo "   2. Try making a small test commit to see the hooks in action"  
echo "   3. Share docs/CONTRIBUTING.md with team members"
echo "   4. Make sure CI/CD is configured if using GitHub Actions"
echo "   5. Remember: CLAUDE.md must be updated for every code change!"
echo ""
print_info "For questions or issues, refer to the troubleshooting sections in:"
print_info "   • PROJECT_RULES.md (comprehensive rules)"
print_info "   • docs/CONTRIBUTING.md (developer workflow)"