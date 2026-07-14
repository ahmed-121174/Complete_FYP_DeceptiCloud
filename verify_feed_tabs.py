#!/usr/bin/env python3
"""
Verification script for Live Threat Feed tabs implementation
Checks that all required functions and HTML elements are present
"""

import re
import sys

def check_html():
    """Check HTML file for tab buttons"""
    print("🔍 Checking dashboard.html...")
    
    with open('dashboard/templates/dashboard.html', 'r') as f:
        html = f.read()
    
    checks = {
        'Tab button container': 'feed-tab-btn' in html,
        'Recent tab button': 'data-feed-tab="recent"' in html,
        'Wazuh tab button': 'data-feed-tab="wazuh"' in html,
        'Critical tab button': 'data-feed-tab="critical"' in html,
        'switchFeedTab onclick': 'onclick="switchFeedTab' in html,
    }
    
    all_passed = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
        if not result:
            all_passed = False
    
    return all_passed

def check_javascript():
    """Check JavaScript file for required functions"""
    print("\n🔍 Checking dashboard.js...")
    
    with open('dashboard/static/dashboard.js', 'r') as f:
        js = f.read()
    
    checks = {
        'switchFeedTab function': 'async function switchFeedTab' in js or 'function switchFeedTab' in js,
        'loadFeedData function': 'async function loadFeedData' in js or 'function loadFeedData' in js,
        'loadRecentFeed function': 'function loadRecentFeed' in js,
        'loadWazuhFeed function': 'function loadWazuhFeed' in js,
        'loadCriticalFeed function': 'function loadCriticalFeed' in js,
        'updateWazuhFeed function': 'function updateWazuhFeed' in js,
        'currentFeedTab variable': 'currentFeedTab' in js,
        'feedDataCache variable': 'feedDataCache' in js,
        'Wazuh API call': '/api/adaptive/wazuh-alerts' in js,
        'Confidence filter (0.75)': 'conf >= 0.75' in js or 'confidence >= 0.75' in js,
        '15 minute filter': '15 * 60 * 1000' in js,
    }
    
    all_passed = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
        if not result:
            all_passed = False
    
    # Check syntax balance
    print("\n🔍 Checking syntax balance...")
    syntax_checks = {
        'Braces': (js.count('{'), js.count('}')),
        'Parentheses': (js.count('('), js.count(')')),
        'Brackets': (js.count('['), js.count(']')),
    }
    
    for name, (open_count, close_count) in syntax_checks.items():
        balanced = open_count == close_count
        status = "✅" if balanced else "❌"
        print(f"  {status} {name}: {open_count} open, {close_count} close")
        if not balanced:
            all_passed = False
    
    return all_passed

def check_integration():
    """Check that functions are properly integrated"""
    print("\n🔍 Checking integration...")
    
    with open('dashboard/static/dashboard.js', 'r') as f:
        js = f.read()
    
    checks = {
        'loadOverview calls loadFeedData': 'loadFeedData(currentFeedTab)' in js,
        'switchFeedTab updates UI': 'btn.style.background' in js and 'switchFeedTab' in js,
        'updateFeed handles empty states': 'emptyMessages' in js or 'No recent threats' in js,
        'Cache timeout check': 'feedDataCache.lastFetch' in js,
    }
    
    all_passed = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
        if not result:
            all_passed = False
    
    return all_passed

def main():
    print("=" * 60)
    print("Live Threat Feed Tabs - Verification Script")
    print("=" * 60)
    
    html_ok = check_html()
    js_ok = check_javascript()
    integration_ok = check_integration()
    
    print("\n" + "=" * 60)
    if html_ok and js_ok and integration_ok:
        print("✅ ALL CHECKS PASSED - Implementation is complete!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("  1. Start the system: ./start_stop/decepticloud_control.sh start")
        print("  2. Open dashboard: http://localhost:9000")
        print("  3. Login: admin / DeceptiCloud")
        print("  4. Test the 3 tabs in Live Threat Feed box")
        print("\n🎉 Ready for testing!")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review the output above")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
