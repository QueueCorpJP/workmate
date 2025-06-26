#!/usr/bin/env python3
"""
Debug script for mojibake fix
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.knowledge.pdf_enhanced import fix_mojibake_text, MOJIBAKE_MAPPING

def debug_fix():
    test_text = "縺薙ｌ縺ｯ繝?繧ｹ繝医〒縺吶?"
    print(f"Original text: {test_text}")
    print(f"Text length: {len(test_text)}")
    
    # Check what's in the mapping
    print("\nMapping keys that match:")
    for key in MOJIBAKE_MAPPING.keys():
        if key in test_text:
            print(f"  '{key}' -> '{MOJIBAKE_MAPPING[key]}'")
    
    # Step by step fix
    fixed_text = test_text
    print(f"\nStep by step fix:")
    print(f"1. Original: {fixed_text}")
    
    # Apply mapping
    sorted_mapping = sorted(MOJIBAKE_MAPPING.items(), key=lambda x: len(x[0]), reverse=True)
    for mojibake, correct in sorted_mapping:
        if mojibake in fixed_text:
            print(f"2. Replacing '{mojibake}' with '{correct}'")
            fixed_text = fixed_text.replace(mojibake, correct)
            print(f"   Result: {fixed_text}")
    
    print(f"\nFinal result: {fixed_text}")
    
    # Now test the actual function
    result = fix_mojibake_text(test_text)
    print(f"Function result: {result}")

if __name__ == "__main__":
    debug_fix()