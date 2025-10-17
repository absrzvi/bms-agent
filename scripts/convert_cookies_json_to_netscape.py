#!/usr/bin/env python3
"""
Convert EditThisCookie JSON format to Netscape cookie format.

Usage:
    python convert_cookies_json_to_netscape.py sharepoint_cookies.txt sharepoint_cookies_netscape.txt
"""

import json
import sys
from pathlib import Path


def json_to_netscape(json_file: Path, output_file: Path):
    """Convert JSON cookies to Netscape format."""
    
    # Read JSON cookies
    with open(json_file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    # Write Netscape format
    with open(output_file, 'w', encoding='utf-8') as f:
        # Netscape header
        f.write("# Netscape HTTP Cookie File\n")
        f.write("# This is a generated file! Do not edit.\n\n")
        
        for cookie in cookies:
            # Extract fields
            domain = cookie.get('domain', '')
            host_only = cookie.get('hostOnly', False)
            path = cookie.get('path', '/')
            secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
            expiration = int(cookie.get('expirationDate', 0))
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            
            # Netscape format: domain, flag, path, secure, expiration, name, value
            # flag: TRUE if domain starts with '.', FALSE otherwise
            flag = 'TRUE' if domain.startswith('.') else 'FALSE'
            
            # Write tab-separated line
            f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}\n")
    
    print(f"✅ Converted {len(cookies)} cookies from JSON to Netscape format")
    print(f"📁 Input:  {json_file}")
    print(f"📁 Output: {output_file}")
    
    # Show key authentication cookies
    auth_cookies = [c['name'] for c in cookies if c['name'] in ['FedAuth', 'rtFa', 'SIMI']]
    if auth_cookies:
        print(f"🔑 Authentication cookies found: {', '.join(auth_cookies)}")
    else:
        print("⚠️  Warning: No FedAuth or rtFa cookies found - authentication may fail")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python convert_cookies_json_to_netscape.py <input.json> <output.txt>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    
    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)
    
    json_to_netscape(input_file, output_file)
