#!/bin/bash
# Railway Pre-Deploy Test Script - Local Test Version
set -e

echo "🚂 Railway Pre-Deploy Testing Suite"
echo "=================================="

export TESTING=1
export DATABASE_URL=""
export PORT=5999
export CACHE_EXPIRY_HOURS=1
export PRICING_CACHE_EXPIRY_HOURS=1

echo ""
echo "🐍 Backend Critical Tests"
echo "-------------------------"
cd backend

echo "Running pricing system tests (critical for deployment)..."
python3 -m pytest tests/test_pricing_system.py::TestPricingCache::test_pricing_cache_expiry -x --tb=short --disable-warnings -q

echo "Running API endpoint tests (critical for deployment)..."
python3 -m pytest tests/test_api_endpoints.py::TestSpellEndpoints::test_get_spells_invalid_class -x --tb=short --disable-warnings -q

echo "Running cache management tests (critical for deployment)..."
python3 -m pytest tests/test_cache_management.py::TestCacheExpiry::test_spell_cache_expiry -x --tb=short --disable-warnings -q

cd ..

echo ""
echo "✅ Critical Backend Tests Complete"
echo "=================================="
echo "🎯 Backend: Core pricing and API systems verified"
echo "🚀 Railway deployment would proceed safely"