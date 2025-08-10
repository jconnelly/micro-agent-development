#!/bin/bash

# Setup script for git hooks
# Run this script to install git hooks for the project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_HOOKS_DIR="$(git rev-parse --git-dir)/hooks"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info "Setting up git hooks for micro-agent-development project..."

# Make hooks executable
chmod +x "$SCRIPT_DIR/pre-commit"
chmod +x "$SCRIPT_DIR/commit-msg"

# Copy hooks to git hooks directory
if [ -f "$GIT_HOOKS_DIR/pre-commit" ]; then
    print_warning "Existing pre-commit hook found. Backing up to pre-commit.backup"
    mv "$GIT_HOOKS_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit.backup"
fi

if [ -f "$GIT_HOOKS_DIR/commit-msg" ]; then
    print_warning "Existing commit-msg hook found. Backing up to commit-msg.backup"
    mv "$GIT_HOOKS_DIR/commit-msg" "$GIT_HOOKS_DIR/commit-msg.backup"
fi

cp "$SCRIPT_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit"
cp "$SCRIPT_DIR/commit-msg" "$GIT_HOOKS_DIR/commit-msg"

chmod +x "$GIT_HOOKS_DIR/pre-commit"
chmod +x "$GIT_HOOKS_DIR/commit-msg"

print_success "Git hooks installed successfully!"

echo ""
print_info "Installed hooks:"
print_info "- pre-commit: Enforces documentation updates for significant changes"
print_info "- commit-msg: Validates commit message format and quality"

echo ""
print_info "Usage:"
print_info "- Hooks will run automatically on each commit"
print_info "- Use 'git commit --no-verify' to skip hooks if needed"
print_info "- Major changes (>50 lines) require CHANGELOG.md updates"
print_info "- Very large changes (>200 lines) may require CLAUDE.md updates"

echo ""
print_success "Setup complete! Your commits will now be validated for documentation standards."