#!/usr/bin/env python
"""
Script to fix the unterminated string in the EnhancedAIService file
"""

import re

def fix_unterminated_string(file_path):
    print(f"Fixing unterminated string in {file_path}")
    
    # Read the file into memory
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a backup
    with open(f"{file_path}.backup", 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created backup at {file_path}.backup")
    
    # Fix the issue by finding the problematic docstring
    pattern = r'async def test_service\(\):\s+"""Test the enhanced AI service."""'
    replacement = r'async def test_service():\n    """Test the enhanced AI service."""'
    
    fixed_content = re.sub(pattern, replacement, content)
    
    # Write the fixed content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("Fixed file written. Check if the issue is resolved.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python fix_script.py <file_path>")
        sys.exit(1)
    
    fix_unterminated_string(sys.argv[1])
