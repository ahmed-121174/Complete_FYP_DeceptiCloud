#!/bin/bash
# Setup script for GeoIP2 database (optional for enhanced fingerprinting)

echo "🌍 GeoIP2 Database Setup for Enhanced Fingerprinting"
echo "===================================================="
echo ""

# Create data directory
mkdir -p data

# Check if database already exists
if [ -f "data/GeoLite2-City.mmdb" ]; then
    echo "✅ GeoLite2-City.mmdb already exists"
    echo "   Location: data/GeoLite2-City.mmdb"
    exit 0
fi

echo "📥 GeoLite2 Database Download Instructions:"
echo ""
echo "The GeoLite2 database is free but requires registration."
echo ""
echo "Steps to download:"
echo "1. Visit: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data"
echo "2. Sign up for a free MaxMind account"
echo "3. Download 'GeoLite2 City' in MMDB format"
echo "4. Extract and place 'GeoLite2-City.mmdb' in the 'data/' directory"
echo ""
echo "Alternative: Use the direct download link (requires MaxMind account):"
echo "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=YOUR_LICENSE_KEY&suffix=tar.gz"
echo ""
echo "⚠️  Note: The fingerprint system works without GeoIP2"
echo "   Locations will show as 'Unknown' if database is not available"
echo ""
echo "After downloading, run:"
echo "  mv /path/to/GeoLite2-City.mmdb data/"
echo ""
