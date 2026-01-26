# Scripts Directory

This directory contains utility scripts for development and testing.

## Available Scripts

### `test_setup.py`
Verifies that all dependencies and services are correctly configured.

**Usage:**
```bash
python scripts/test_setup.py
```

**What it checks:**
- Python version and dependencies
- Environment variables
- Azure OpenAI connection
- Pinecone connection  
- Google Vision API credentials
- File system permissions

---

## Adding New Scripts

When adding new utility scripts:
1. Place them in this `scripts/` directory
2. Add a brief description here
3. Include usage examples
4. Make scripts executable if they're shell scripts: `chmod +x script.sh`

---

## Best Practices

- ✅ Keep scripts focused on a single task
- ✅ Add error handling
- ✅ Include help text (`--help` flag)
- ✅ Document environment variables needed
- ✅ Test scripts before committing
