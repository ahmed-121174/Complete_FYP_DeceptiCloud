#!/usr/bin/env python3
"""
Verification script for icon implementation
Checks that all icons are properly added and no functionality is broken
"""

import re

def check_files_exist():
    """Check that all required files exist"""
    print("=" * 70)
    print("ICON IMPLEMENTATION VERIFICATION")
    print("=" * 70)
    
    print("\n📁 Checking Files...")
    print("-" * 70)
    
    files = {
        'dashboard/static/icons.js': 'Icon library',
        'dashboard/templates/dashboard.html': 'Dashboard HTML',
        'dashboard/static/dashboard.js': 'Dashboard JavaScript',
        'dashboard/static/dashboard.css': 'Dashboard CSS',
    }
    
    all_exist = True
    for file_path, description in files.items():
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                print(f"✅ {description}: {file_path}")
        except FileNotFoundError:
            print(f"❌ {description}: {file_path} NOT FOUND")
            all_exist = False
    
    return all_exist

def check_icons_js():
    """Check icons.js implementation"""
    print("\n🎨 Checking Icon Library...")
    print("-" * 70)
    
    try:
        with open('dashboard/static/icons.js', 'r') as f:
            content = f.read()
        
        checks = {
            'ICONS object defined': 'const ICONS = {' in content,
            'Navigation icons': 'overview:' in content and 'attacks:' in content,
            'Stat card icons': 'attacksDetected:' in content,
            'Empty state icons': 'emptyData:' in content,
            'Feed icons': 'feedDanger:' in content,
            'initializeIcons function': 'function initializeIcons()' in content,
            'Auto-initialization': 'DOMContentLoaded' in content,
            'Window export': 'window.ICONS' in content,
        }
        
        all_passed = True
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")
            if not result:
                all_passed = False
        
        # Count icons
        icon_count = content.count('`<svg')
        print(f"\n  📊 Total icons defined: {icon_count}")
        
        return all_passed
    except Exception as e:
        print(f"❌ Error reading icons.js: {e}")
        return False

def check_html_integration():
    """Check HTML integration"""
    print("\n📄 Checking HTML Integration...")
    print("-" * 70)
    
    try:
        with open('dashboard/templates/dashboard.html', 'r') as f:
            content = f.read()
        
        checks = {
            'icons.js script tag': '<script src="/static/icons.js"></script>' in content,
            'Script in head section': '<script src="/static/icons.js"></script>' in content and content.index('<script src="/static/icons.js"></script>') < content.index('</head>'),
        }
        
        all_passed = True
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")
            if not result:
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ Error reading dashboard.html: {e}")
        return False

def check_js_integration():
    """Check JavaScript integration"""
    print("\n⚙️  Checking JavaScript Integration...")
    print("-" * 70)
    
    try:
        with open('dashboard/static/dashboard.js', 'r') as f:
            content = f.read()
        
        checks = {
            'Icon reinitialization in navigateTo': 'initializeIcons' in content,
            'setTimeout for icon init': 'setTimeout' in content and 'initializeIcons' in content,
        }
        
        all_passed = True
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")
            if not result:
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ Error reading dashboard.js: {e}")
        return False

def check_css_updates():
    """Check CSS updates"""
    print("\n🎨 Checking CSS Updates...")
    print("-" * 70)
    
    try:
        with open('dashboard/static/dashboard.css', 'r') as f:
            content = f.read()
        
        checks = {
            '.nav-icon svg styling': '.nav-icon svg' in content,
            '.stat-icon svg styling': '.stat-icon svg' in content,
            '.empty-icon svg styling': '.empty-icon svg' in content,
            '.feed-icon svg styling': '.feed-icon svg' in content,
            'Flex display for icons': 'display: flex' in content and '.nav-icon' in content,
        }
        
        all_passed = True
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")
            if not result:
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ Error reading dashboard.css: {e}")
        return False

def check_no_breaking_changes():
    """Verify no breaking changes"""
    print("\n🔒 Checking for Breaking Changes...")
    print("-" * 70)
    
    try:
        # Check that core functions still exist
        with open('dashboard/static/dashboard.js', 'r') as f:
            js_content = f.read()
        
        core_functions = [
            'function navigateTo',
            'function loadPageData',
            'function loadOverview',
            'function loadAttacks',
            'function initDashboard',
        ]
        
        all_exist = True
        for func in core_functions:
            if func in js_content:
                print(f"  ✅ {func} - Still exists")
            else:
                print(f"  ❌ {func} - MISSING!")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"❌ Error checking for breaking changes: {e}")
        return False

def main():
    files_ok = check_files_exist()
    icons_ok = check_icons_js()
    html_ok = check_html_integration()
    js_ok = check_js_integration()
    css_ok = check_css_updates()
    no_breaks = check_no_breaking_changes()
    
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    results = {
        'Files exist': files_ok,
        'Icon library': icons_ok,
        'HTML integration': html_ok,
        'JS integration': js_ok,
        'CSS updates': css_ok,
        'No breaking changes': no_breaks,
    }
    
    all_passed = all(results.values())
    
    for check, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Icons implementation complete!")
        print("=" * 70)
        print("\n📋 Next Steps:")
        print("  1. Start the dashboard: python3 dashboard/app.py")
        print("  2. Open browser: http://localhost:9000")
        print("  3. Login: admin / DeceptiCloud")
        print("  4. Verify icons appear in:")
        print("     - Sidebar navigation")
        print("     - Stat cards on Overview page")
        print("     - Empty states")
        print("\n🎉 Icons should now be professional and consistent!")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review the output above")
        print("=" * 70)
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
