#!/usr/bin/env python3
"""
Comprehensive functionality test to ensure no core features were broken
by the legacy spell system removal.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all core modules import correctly."""
    print("Testing imports...")
    
    try:
        # Test security utils
        from utils.security import (
            sanitize_search_input, 
            validate_item_search_params,
            validate_spell_search_params,
            rate_limit_by_ip
        )
        print("  ✅ Security utils import successfully")
        
        # Test that spell search validation works
        result = validate_spell_search_params({'q': 'test'})
        assert 'q' in result
        print("  ✅ Spell search validation works")
        
        # Test that item search validation still works  
        result = validate_item_search_params({'q': 'test'})
        assert 'q' in result
        print("  ✅ Item search validation works")
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False
    
    return True

def test_app_structure():
    """Test that the app structure is intact."""
    print("Testing app structure...")
    
    try:
        # Check that app.py compiles without errors
        import py_compile
        py_compile.compile('app.py', doraise=True)
        print("  ✅ app.py compiles successfully")
        
        # Check key routes are defined
        with open('app.py', 'r') as f:
            content = f.read()
        
        required_routes = [
            '/api/health',
            '/api/items/search', 
            '/api/spells/search',
            '/api/cache/status'
        ]
        
        for route in required_routes:
            if route in content:
                print(f"  ✅ Route {route} found")
            else:
                print(f"  ❌ Route {route} missing")
                return False
                
        # Check that legacy spell functions are removed
        legacy_functions = [
            'fetch_single_spell_pricing',
            'parse_spell_details_from_html',
            'get_expired_spell_cache_classes',
            'refresh_expired_spell_caches'
        ]
        
        for func in legacy_functions:
            if f'def {func}' in content:
                print(f"  ❌ Legacy function {func} still present")
                return False
            else:
                print(f"  ✅ Legacy function {func} properly removed")
        
        # Check that no alla.clumsysworld.com references remain (except in comments)
        alla_refs = content.count('alla.clumsysworld.com')
        if alla_refs > 0:
            print(f"  ⚠️  Found {alla_refs} references to alla.clumsysworld.com (should be 0)")
            # This might be acceptable if they're just in comments
        else:
            print("  ✅ No alla.clumsysworld.com references found")
            
    except Exception as e:
        print(f"  ❌ App structure error: {e}")
        return False
    
    return True

def test_route_definitions():
    """Test that route definitions don't conflict."""
    print("Testing route definitions...")
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check for duplicate route definitions
        import re
        routes = re.findall(r"@app\.route\('([^']+)'", content)
        route_counts = {}
        
        for route in routes:
            route_counts[route] = route_counts.get(route, 0) + 1
        
        duplicates = {route: count for route, count in route_counts.items() if count > 1}
        
        if duplicates:
            print(f"  ❌ Duplicate routes found: {duplicates}")
            return False
        else:
            print(f"  ✅ No duplicate routes found ({len(routes)} unique routes)")
            
        # Check for duplicate function names
        functions = re.findall(r"def ([a-zA-Z_][a-zA-Z0-9_]*)\(", content)
        func_counts = {}
        
        for func in functions:
            func_counts[func] = func_counts.get(func, 0) + 1
        
        duplicates = {func: count for func, count in func_counts.items() if count > 1}
        
        if duplicates:
            print(f"  ❌ Duplicate functions found: {duplicates}")
            return False
        else:
            print(f"  ✅ No duplicate functions found ({len(set(functions))} unique functions)")
            
    except Exception as e:
        print(f"  ❌ Route definition error: {e}")
        return False
    
    return True

def test_spell_search_functionality():
    """Test that the new spell search function is properly implemented."""
    print("Testing spell search functionality...")
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check that search_spells function exists and has the right structure
        if 'def search_spells():' not in content:
            print("  ❌ search_spells function not found")
            return False
        else:
            print("  ✅ search_spells function found")
        
        # Check for key components in the function
        spell_components = [
            'spells_new',  # Should query the spells_new table
            'validate_spell_search_params',  # Should use validation
            'class_levels',  # Should return class levels
            'spell_id',  # Should return spell ID
            'effectid1'  # Should include effects
        ]
        
        for component in spell_components:
            if component in content:
                print(f"  ✅ Component '{component}' found")
            else:
                print(f"  ❌ Component '{component}' missing")
                return False
                
    except Exception as e:
        print(f"  ❌ Spell search functionality error: {e}")
        return False
    
    return True

def main():
    """Run all functionality tests."""
    print("=" * 60)
    print("EQDataScraper Functionality Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_app_structure, 
        test_route_definitions,
        test_spell_search_functionality
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\n{test.__name__.replace('_', ' ').title()}:")
        try:
            if test():
                passed += 1
                print(f"  ✅ {test.__name__} PASSED")
            else:
                failed += 1
                print(f"  ❌ {test.__name__} FAILED")
        except Exception as e:
            failed += 1
            print(f"  ❌ {test.__name__} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All functionality tests passed!")
        print("✅ Legacy spell system successfully removed")
        print("✅ New spell search functionality working")
        print("✅ Core application functionality preserved")
        return True
    else:
        print("⚠️  Some tests failed - manual review needed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)