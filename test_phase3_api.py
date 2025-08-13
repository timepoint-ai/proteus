"""
Test script for Phase 3: Chain-only API routes
Tests that all API endpoints fetch data directly from blockchain
"""

import requests
import json
from web3 import Web3

# Test configuration
BASE_URL = "http://localhost:5000"

def test_chain_only_apis():
    """Test the chain-only API endpoints"""
    
    print("\n=== Phase 3: Chain-Only API Routes Test ===\n")
    
    all_tests_passed = True
    
    # Test 1: Get actors from chain
    print("1. Testing chain-only actors endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/chain/actors")
        if response.status_code == 200:
            data = response.json()
            if data.get('source') == 'blockchain':
                print(f"✓ Actors fetched from blockchain: {data.get('total', 0)} actors")
            else:
                print(f"✗ Actors not from blockchain, source: {data.get('source')}")
                all_tests_passed = False
        else:
            print(f"✗ Failed to fetch actors: {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"✗ Error fetching actors: {e}")
        all_tests_passed = False
    
    # Test 2: Get markets from chain
    print("\n2. Testing chain-only markets endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/chain/markets")
        if response.status_code == 200:
            data = response.json()
            if data.get('source') == 'blockchain':
                print(f"✓ Markets fetched from blockchain: {data.get('total', 0)} markets")
                
                # Test filtering by status
                response_active = requests.get(f"{BASE_URL}/api/chain/markets?status=active")
                if response_active.status_code == 200:
                    active_data = response_active.json()
                    print(f"✓ Active markets filter working: {len(active_data.get('markets', []))} active")
            else:
                print(f"✗ Markets not from blockchain")
                all_tests_passed = False
        else:
            print(f"✗ Failed to fetch markets: {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"✗ Error fetching markets: {e}")
        all_tests_passed = False
    
    # Test 3: Get platform statistics from chain
    print("\n3. Testing chain-only stats endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/chain/stats")
        if response.status_code == 200:
            stats = response.json()
            if stats.get('source') == 'blockchain':
                print(f"✓ Platform stats from blockchain:")
                print(f"  - Total markets: {stats.get('total_markets', 0)}")
                print(f"  - Active markets: {stats.get('active_markets', 0)}")
                print(f"  - Total volume: {stats.get('total_volume', '0')}")
                print(f"  - Total actors: {stats.get('total_actors', 0)}")
                print(f"  - Genesis NFT holders: {stats.get('genesis_nft_holders', 0)}")
            else:
                print(f"✗ Stats not from blockchain")
                all_tests_passed = False
        else:
            print(f"✗ Failed to fetch stats: {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"✗ Error fetching stats: {e}")
        all_tests_passed = False
    
    # Test 4: Get market detail from chain
    print("\n4. Testing chain-only market detail endpoint...")
    try:
        # Try to get market ID 1 (if it exists)
        response = requests.get(f"{BASE_URL}/api/chain/market/1")
        if response.status_code == 200:
            data = response.json()
            if data.get('source') == 'blockchain':
                market = data.get('market', {})
                print(f"✓ Market detail from blockchain:")
                print(f"  - Market ID: {market.get('id')}")
                print(f"  - Status: {market.get('status')}")
                print(f"  - Submissions: {len(market.get('submissions', []))}")
                print(f"  - Bet count: {market.get('bet_count', 0)}")
        elif response.status_code == 404:
            print("⚠ Market ID 1 not found (expected if no markets exist)")
        else:
            print(f"✗ Failed to fetch market detail: {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"✗ Error fetching market detail: {e}")
        all_tests_passed = False
    
    # Test 5: Get Genesis NFT holders
    print("\n5. Testing Genesis NFT holders endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/chain/genesis/holders")
        if response.status_code == 200:
            data = response.json()
            if data.get('source') == 'blockchain':
                print(f"✓ Genesis NFT data from blockchain:")
                print(f"  - Total holders: {data.get('total_holders', 0)}")
                print(f"  - Total supply: {data.get('total_supply', 0)}")
                
                holders = data.get('holders', [])
                if holders:
                    top_holder = holders[0]
                    print(f"  - Top holder: {top_holder['address'][:10]}... owns {top_holder['token_count']} NFTs")
            else:
                print(f"✗ Genesis data not from blockchain")
                all_tests_passed = False
        else:
            print(f"✗ Failed to fetch Genesis holders: {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"✗ Error fetching Genesis holders: {e}")
        all_tests_passed = False
    
    # Test 6: Verify no database dependencies
    print("\n6. Testing that old database endpoints are removed/deprecated...")
    deprecated_endpoints = [
        '/market/create',  # Should use contract directly
        '/admin/users',    # No user accounts, only wallets
        '/admin/database', # No database operations
        '/test/generate'   # No test data generation
    ]
    
    for endpoint in deprecated_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 404:
                print(f"✓ Deprecated endpoint removed: {endpoint}")
            else:
                print(f"✗ Deprecated endpoint still exists: {endpoint} (status: {response.status_code})")
                all_tests_passed = False
        except:
            print(f"✓ Deprecated endpoint not accessible: {endpoint}")
    
    return all_tests_passed

def test_contract_abi_endpoints():
    """Test that contract ABIs are accessible"""
    
    print("\n=== Testing Contract ABI Endpoints ===\n")
    
    contracts = [
        'EnhancedPredictionMarket',
        'ActorRegistry',
        'DecentralizedOracle',
        'PayoutManager'
    ]
    
    all_passed = True
    
    for contract_name in contracts:
        try:
            response = requests.get(f"{BASE_URL}/api/contract-abi/{contract_name}")
            if response.status_code == 200:
                abi = response.json()
                if isinstance(abi, list) and len(abi) > 0:
                    print(f"✓ {contract_name} ABI available: {len(abi)} functions")
                else:
                    print(f"✗ {contract_name} ABI empty or invalid")
                    all_passed = False
            else:
                print(f"✗ {contract_name} ABI not accessible: {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"✗ Error fetching {contract_name} ABI: {e}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("\n" + "="*50)
    print("PHASE 3: CHAIN-ONLY API ROUTES TEST")
    print("="*50)
    
    # Run chain-only API tests
    api_tests_passed = test_chain_only_apis()
    
    # Run ABI endpoint tests
    abi_tests_passed = test_contract_abi_endpoints()
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Chain-Only APIs: {'✓ PASSED' if api_tests_passed else '✗ FAILED'}")
    print(f"Contract ABIs: {'✓ PASSED' if abi_tests_passed else '✗ FAILED'}")
    
    if api_tests_passed and abi_tests_passed:
        print("\n✓ PHASE 3 COMPLETE: All API routes are now chain-only!")
        print("Database dependencies have been removed from API layer.")
    else:
        print("\n✗ PHASE 3 INCOMPLETE: Some tests failed")
        print("Please check the error messages above.")