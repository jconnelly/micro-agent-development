#!/bin/bash

# Sync CHANGELOG.md with docs/about/changelog.md
# This script ensures both changelog files stay in sync

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MAIN_CHANGELOG="$PROJECT_ROOT/CHANGELOG.md"
DOCS_CHANGELOG="$PROJECT_ROOT/docs/about/changelog.md"

print_info "Synchronizing changelog files..."

# Check if main CHANGELOG.md exists
if [ ! -f "$MAIN_CHANGELOG" ]; then
    print_error "Main CHANGELOG.md not found at: $MAIN_CHANGELOG"
    exit 1
fi

# Create docs directory if it doesn't exist
mkdir -p "$(dirname "$DOCS_CHANGELOG")"

# Function to convert CHANGELOG.md to docs format
convert_changelog_to_docs() {
    local input_file="$1"
    local output_file="$2"
    
    print_info "Converting $input_file to docs format..."
    
    cat > "$output_file" << 'EOF'
# Micro-Agent Development Platform Changelog

!!! info "Changelog Synchronization"
    This changelog is automatically synchronized with the main CHANGELOG.md file.
    All updates are made to the root CHANGELOG.md and automatically reflected here.

EOF

    # Convert the main changelog content to docs format with admonitions
    awk '
    BEGIN { in_unreleased = 0; in_version = 0; version_content = ""; version_title = "" }
    
    /^# Changelog/ { next }  # Skip main title
    
    /^## \[Unreleased\]/ {
        in_unreleased = 1
        print "!!! note \"Unreleased Changes\""
        print "    "
        print "    The following changes are in development and will be included in the next release:"
        print "    "
        next
    }
    
    /^## \[/ && !/Unreleased/ {
        # End previous version block if any
        if (in_version) {
            print version_content
            print ""
        }
        
        in_unreleased = 0
        in_version = 1
        
        # Extract version and date
        match($0, /## \[([^\]]+)\] - (.+)/, arr)
        if (arr[1] && arr[2]) {
            version_title = "!!! success \"Version " arr[1] " - " arr[2] "\""
            version_content = version_title "\n    "
        } else {
            version_title = "!!! success \"" $0 "\""
            version_content = version_title "\n    "
        }
        next
    }
    
    /^### / {
        if (in_unreleased) {
            gsub(/^### /, "    **", $0)
            $0 = $0 "**:"
            print "    " $0
        } else if (in_version) {
            gsub(/^### /, "    **", $0)
            $0 = $0 "**:"
            version_content = version_content "\n    " $0
        }
        next
    }
    
    /^- / {
        if (in_unreleased) {
            print "    " $0
        } else if (in_version) {
            version_content = version_content "\n    " $0
        }
        next
    }
    
    /^$/ {
        if (in_unreleased) {
            print "    "
        } else if (in_version) {
            version_content = version_content "\n    "
        }
        next
    }
    
    # Regular content
    {
        if (in_unreleased) {
            print "    " $0
        } else if (in_version) {
            version_content = version_content "\n    " $0
        } else if (NF > 0) {  # Non-empty line outside sections
            print $0
        }
    }
    
    END {
        # Print final version block
        if (in_version && version_content) {
            print version_content
            print ""
        }
    }
    ' "$input_file" >> "$output_file"
    
    # Add footer
    cat >> "$output_file" << 'EOF'

---

!!! tip "Contributing"
    To add entries to this changelog:
    
    1. Edit the main `CHANGELOG.md` file in the project root
    2. Add your entry under the `[Unreleased]` section
    3. Run `scripts/sync-changelog.sh` to update this docs version
    4. The sync happens automatically during git commits

!!! info "Format Guidelines"
    
    Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:
    
    - **Added** for new features
    - **Changed** for changes in existing functionality  
    - **Deprecated** for soon-to-be removed features
    - **Removed** for now removed features
    - **Fixed** for any bug fixes
    - **Security** for vulnerability fixes

EOF
}

# Check if files are different
if [ -f "$DOCS_CHANGELOG" ]; then
    # Create temporary converted file
    TEMP_CONVERTED=$(mktemp)
    convert_changelog_to_docs "$MAIN_CHANGELOG" "$TEMP_CONVERTED"
    
    if cmp -s "$TEMP_CONVERTED" "$DOCS_CHANGELOG"; then
        print_success "Changelog files are already in sync"
        rm "$TEMP_CONVERTED"
        exit 0
    else
        print_warning "Changelog files are out of sync, updating docs version..."
        mv "$TEMP_CONVERTED" "$DOCS_CHANGELOG"
    fi
else
    print_info "Creating docs changelog for the first time..."
    convert_changelog_to_docs "$MAIN_CHANGELOG" "$DOCS_CHANGELOG"
fi

print_success "Changelog synchronization complete!"
print_info "Files synchronized:"
print_info "  Source: $MAIN_CHANGELOG"
print_info "  Target: $DOCS_CHANGELOG"

# If running in git hook context, add the updated file
if [ "$1" = "--git-add" ]; then
    git add "$DOCS_CHANGELOG"
    print_success "Updated docs/about/changelog.md added to git staging"
fi