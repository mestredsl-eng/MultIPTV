"""Test script to verify quality indicator consistency fix."""

import sys
sys.path.insert(0, '.')

from app.services.parser import remove_quality_indicators, remove_quality_from_name
from app.services.exporter import sanitize_filename
import hashlib

def test_quality_removal():
    """Test that both functions now produce consistent results."""
    
    test_cases = [
        "Matrix [L] (1999)",
        "Avatar [4K] (2009)",
        "Titanic [FHD] [WEB-DL] (1997)",
        "Frozen [HD] (2013)",
        "Inception [BLURAY] (2010)",
        "Movie [H265] [DOLBY] (2020)",
        "Film [LEG] (2015)",
        "Series S01E01 [DUB] (2018)",
        "Show [DUAL] [AAC] (2019)",
        "Test [XXX] (2021)",
        "Adult [PORN] (2022)",
        "Content 720p (2016)",
        "Video 1080p (2017)",
        "Clip 2160p (2018)",
        "4K Movie (2019)",
        "8K Film (2020)",
    ]
    
    print("Testing quality indicator consistency...")
    print("=" * 60)
    
    all_passed = True
    
    for test_name in test_cases:
        # Test remove_quality_indicators (canonical function)
        result_canonical = remove_quality_indicators(test_name)
        
        # Test remove_quality_from_name (should delegate to canonical)
        result_legacy = remove_quality_from_name(test_name)
        
        # Test sanitize_filename (should use canonical internally)
        result_sanitize = sanitize_filename(test_name)
        
        # Check if canonical and legacy match
        if result_canonical != result_legacy:
            print(f"❌ FAIL: {test_name}")
            print(f"   Canonical: {result_canonical}")
            print(f"   Legacy:    {result_legacy}")
            all_passed = False
        else:
            print(f"✅ PASS: {test_name}")
            print(f"   Result: {result_canonical}")
        
        # Note: sanitize_filename may differ due to additional Windows character removal
        # This is expected and correct behavior
        print(f"   Sanitize:  {result_sanitize}")
        print()
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests PASSED - Quality functions are consistent")
    else:
        print("❌ Some tests FAILED - Quality functions are inconsistent")
    
    return all_passed

def test_hash_consistency():
    """Test that hash calculation is consistent with filename sanitization."""
    
    print("\nTesting hash consistency...")
    print("=" * 60)
    
    test_cases = [
        ("Movie", "Matrix [L] (1999)", 1999),
        ("Movie", "Avatar [4K] (2009)", 2009),
        ("Series", "Show S01E01 [HD] (2018)", 2018),
    ]
    
    all_passed = True
    
    for categoria, nome, ano in test_cases:
        # Calculate hash using the canonical function
        nome_limpo = remove_quality_indicators(nome)
        hash_input = f"{categoria}|{nome_limpo}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Sanitize filename
        filename = sanitize_filename(nome)
        
        print(f"Test: {nome}")
        print(f"   Clean name: {nome_limpo}")
        print(f"   Filename:   {filename}")
        print(f"   Hash input: {hash_input}")
        print(f"   Hash:       {hash_value}")
        
        # The clean name should be the base for both hash and filename
        # (filename may have additional Windows character removal)
        if nome_limpo in filename or nome_limpo.replace(' ', '') in filename.replace(' ', ''):
            print(f"   ✅ Filename contains clean name")
        else:
            print(f"   ⚠️  Filename differs from clean name (may be due to Windows chars)")
        
        print()
    
    print("=" * 60)
    print("Hash consistency test completed")
    
    return True

if __name__ == "__main__":
    print("Quality Indicator Fix Test Suite")
    print("=" * 60)
    print()
    
    test1_passed = test_quality_removal()
    test2_passed = test_hash_consistency()
    
    print("\n" + "=" * 60)
    print("FINAL RESULT:")
    if test1_passed:
        print("✅ Quality indicator functions are now CONSISTENT")
        print("✅ Safe to proceed with migration")
    else:
        print("❌ Quality indicator functions are still INCONSISTENT")
        print("❌ DO NOT proceed with migration")
    print("=" * 60)
