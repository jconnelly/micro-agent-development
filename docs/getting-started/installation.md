# Installation Guide

Complete installation instructions for production and development environments.

## 📋 System Requirements

### Minimum Requirements

- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.9 or higher (3.11+ recommended for best performance)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 1GB free space for installation and dependencies
- **Network**: Internet connection for API calls and package installation

### Recommended Production Environment

- **Python**: 3.11+ with virtual environment
- **Memory**: 16GB+ RAM for large-scale processing
- **CPU**: Multi-core processor for parallel processing
- **Storage**: SSD for faster I/O operations
- **Network**: High-bandwidth connection for API-intensive workloads

## 🛠️ Installation Methods

### Method 1: Standard Installation (Recommended)

#### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/jconnelly/micro-agent-development.git
cd micro-agent-development

# Verify Python version
python --version
# Should show Python 3.9+ (e.g., Python 3.11.5)
```

#### Step 2: Create Virtual Environment (Recommended)

=== "Windows"
    
    ```cmd
    # Create virtual environment
    python -m venv venv
    
    # Activate virtual environment
    venv\Scripts\activate
    
    # Verify activation (should show (venv) in prompt)
    ```

=== "macOS/Linux"
    
    ```bash
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Verify activation (should show (venv) in prompt)
    ```

#### Step 3: Install Dependencies

```bash
# Upgrade pip to latest version
pip install --upgrade pip

# Install all required dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(google-generativeai|pyyaml|mkdocs)"
```

**Expected Dependencies:**
- `google-generativeai>=0.3.0` - Google Gemini AI integration
- `PyYAML>=6.0.1` - Configuration file parsing
- `python-dotenv>=1.0.0` - Environment variable management
- `mkdocs>=1.6.0` - Documentation system
- `mkdocs-material>=9.6.0` - Material Design theme

### Method 2: Development Installation

For contributors and developers who want to modify the codebase:

```bash
# Clone with full git history
git clone https://github.com/jconnelly/micro-agent-development.git
cd micro-agent-development

# Create development environment
python -m venv dev-venv
source dev-venv/bin/activate  # On Windows: dev-venv\Scripts\activate

# Install with development dependencies
pip install -r requirements.txt

# Install additional development tools (optional)
pip install pytest black flake8 mypy

# Verify development setup
python -c "from Agents import BusinessRuleExtractionAgent; print('✅ Development setup complete')"
```

### Method 3: Docker Installation (Advanced)

For containerized deployment:

```dockerfile
# Create Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["python", "-m", "your_application"]
```

```bash
# Build and run
docker build -t micro-agent-platform .
docker run -d -p 8000:8000 -e GOOGLE_API_KEY=your_key micro-agent-platform
```

## 🔑 API Configuration

### Google Generative AI Setup

1. **Get API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Click "Create API Key"
   - Copy your API key (keep it secure!)

2. **Set Environment Variables**

=== "Production (Recommended)"
    
    Create `.env` file in project root:
    ```bash
    # .env file (never commit to git!)
    GOOGLE_API_KEY=your_actual_api_key_here
    ENVIRONMENT=production
    LOG_LEVEL=INFO
    ```

=== "Development"
    
    ```bash
    # Set temporarily for testing
    export GOOGLE_API_KEY="your_api_key_here"
    
    # On Windows:
    set GOOGLE_API_KEY=your_api_key_here
    ```

=== "System-wide (Unix/Linux)"
    
    ```bash
    # Add to ~/.bashrc or ~/.profile
    echo 'export GOOGLE_API_KEY="your_api_key_here"' >> ~/.bashrc
    source ~/.bashrc
    ```

### Configuration Files

The platform uses YAML configuration files in the `config/` directory:

```bash
# Copy example configurations
cp config/agent_defaults.yaml.example config/agent_defaults.yaml
cp config/domains.yaml.example config/domains.yaml  # if exists
cp config/pii_patterns.yaml.example config/pii_patterns.yaml  # if exists

# Edit configurations as needed
# Use your preferred text editor
vim config/agent_defaults.yaml
```

## ✅ Verify Installation

### Quick Verification Test

Create `verify_installation.py`:

```python
#!/usr/bin/env python3
"""
Installation verification script for Micro-Agent Development Platform
"""

import sys
import os
from pathlib import Path

def test_python_version():
    """Test Python version compatibility"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires 3.9+")
        return False

def test_dependencies():
    """Test required dependencies"""
    required_packages = [
        'google.generativeai',
        'yaml',
        'dotenv',
        'mkdocs'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} - Available")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing.append(package)
    
    return len(missing) == 0

def test_agent_imports():
    """Test agent module imports"""
    try:
        from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
        from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent
        from Agents.PersonalDataProtectionAgent import PersonalDataProtectionAgent
        print("✅ All agent modules - Importable")
        return True
    except ImportError as e:
        print(f"❌ Agent imports failed: {e}")
        return False

def test_configuration():
    """Test configuration files"""
    config_dir = Path("config")
    if config_dir.exists():
        print("✅ Configuration directory - Exists")
        
        required_configs = ["agent_defaults.yaml", "domains.yaml", "pii_patterns.yaml"]
        for config_file in required_configs:
            if (config_dir / config_file).exists():
                print(f"✅ {config_file} - Found")
            else:
                print(f"⚠️  {config_file} - Missing (will use defaults)")
        return True
    else:
        print("❌ Configuration directory - Missing")
        return False

def test_api_key():
    """Test API key configuration"""
    api_key = os.environ.get('GOOGLE_API_KEY')
    if api_key:
        print("✅ GOOGLE_API_KEY - Set")
        return True
    else:
        print("⚠️  GOOGLE_API_KEY - Not set (required for functionality)")
        return False

def main():
    """Run all verification tests"""
    print("🔍 Verifying Micro-Agent Development Platform Installation...")
    print("=" * 60)
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies), 
        ("Agent Imports", test_agent_imports),
        ("Configuration", test_configuration),
        ("API Key", test_api_key)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}:")
        results.append(test_func())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 Installation Complete! ({passed}/{total} tests passed)")
        print("\nNext steps:")
        print("1. Run the Quick Start guide: docs/getting-started/quickstart.md")
        print("2. Explore the documentation: mkdocs serve")
        print("3. Try the example scripts in examples/")
    else:
        print(f"⚠️  Installation Issues Found ({passed}/{total} tests passed)")
        print("\nPlease fix the issues above before proceeding.")
        print("See troubleshooting guide: docs/getting-started/installation.md#troubleshooting")

if __name__ == "__main__":
    main()
```

Run the verification:

```bash
python verify_installation.py
```

### Manual Verification

Test individual components:

```bash
# Test Python imports
python -c "from Agents import BusinessRuleExtractionAgent; print('✅ Agents module working')"

# Test configuration loading
python -c "from Utils import config_loader; print('✅ Configuration system working')"

# Test documentation build
mkdocs build --quiet && echo "✅ Documentation system working"

# Test API connectivity (requires API key)
python -c "import google.generativeai as genai; print('✅ Google AI SDK working')"
```

## 🚀 Post-Installation

### Performance Optimization

For production environments:

```bash
# Set Python optimization
export PYTHONOPTIMIZE=1

# Configure logging
export LOG_LEVEL=INFO

# Set memory limits if needed
export PYTHON_MEMORY_LIMIT=8GB
```

### Security Hardening

1. **API Key Security**
   ```bash
   # Set restrictive permissions on .env file
   chmod 600 .env
   
   # Never commit .env to version control
   echo ".env" >> .gitignore
   ```

2. **File Permissions**
   ```bash
   # Secure configuration directory
   chmod -R 644 config/
   chmod 755 config/
   ```

### Documentation Setup

Build and serve documentation locally:

```bash
# Build documentation
mkdocs build

# Serve documentation (development)
mkdocs serve --dev-addr=127.0.0.1:8001

# Access at: http://127.0.0.1:8001
```

## 🆘 Troubleshooting

### Common Installation Issues

!!! error "Python Version Mismatch"
    
    **Problem:** `ERROR: This package requires Python >=3.9`
    
    **Solutions:**
    - Install Python 3.9+ from [python.org](https://python.org)
    - Use `python3` instead of `python` on Unix systems
    - Consider using `pyenv` for Python version management

!!! error "Dependency Conflicts"
    
    **Problem:** `ERROR: pip's dependency resolver does not currently consider all the packages that are installed`
    
    **Solutions:**
    ```bash
    # Clean install in fresh virtual environment
    rm -rf venv/
    python -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

!!! error "Import Errors"
    
    **Problem:** `ModuleNotFoundError: No module named 'Agents'`
    
    **Solutions:**
    - Ensure you're in the project root directory
    - Check that `Agents/__init__.py` exists
    - Verify PYTHONPATH: `export PYTHONPATH=$PYTHONPATH:.`

!!! error "Permission Denied"
    
    **Problem:** `PermissionError: [Errno 13] Permission denied`
    
    **Solutions:**
    ```bash
    # User installation
    pip install --user -r requirements.txt
    
    # Fix file permissions
    chmod -R 755 .
    ```

### Platform-Specific Issues

=== "Windows"
    
    **Long Path Issues:**
    - Enable long paths in Windows (Group Policy or Registry)
    - Use shorter directory names
    
    **PowerShell Execution Policy:**
    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    ```

=== "macOS"
    
    **SSL Certificate Issues:**
    ```bash
    # Update certificates
    /Applications/Python\ 3.x/Install\ Certificates.command
    ```
    
    **Homebrew Python Issues:**
    ```bash
    # Use system Python or pyenv
    brew install pyenv
    pyenv install 3.11.5
    ```

=== "Linux"
    
    **System Package Dependencies:**
    ```bash
    # Ubuntu/Debian
    sudo apt-get install python3-venv python3-pip python3-dev
    
    # CentOS/RHEL
    sudo yum install python3-venv python3-pip python3-devel
    ```

### Getting Help

If you encounter issues not covered here:

1. **Check the logs** in the project directory
2. **Search existing issues** on [GitHub](https://github.com/jconnelly/micro-agent-development/issues)
3. **Create a new issue** with:
   - Your operating system and Python version
   - Complete error message
   - Steps to reproduce
   - Output of `pip list`

---

**✅ Installation Complete!** 

Your Micro-Agent Development Platform is now ready for production use.

*Next: [Configuration Guide](configuration.md) for customizing your deployment →*