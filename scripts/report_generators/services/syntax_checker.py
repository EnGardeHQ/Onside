#!/usr/bin/env python
"""
Simple syntax checker to help find the unterminated triple-quoted string
"""

import tokenize
from io import BytesIO

def scan_file_for_syntax(filename):
    with open(filename, 'rb') as file:
        try:
            tokens = list(tokenize.tokenize(file.readline))
            print(f"Successful tokenization: No syntax errors found")
        except tokenize.TokenError as e:
            print(f"TokenError: {e}")
        except IndentationError as e:
            print(f"IndentationError: {e}")
        except SyntaxError as e:
            print(f"SyntaxError: {e}")
        except Exception as e:
            print(f"Other error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python syntax_checker.py <filename>")
        sys.exit(1)
    
    scan_file_for_syntax(sys.argv[1])
