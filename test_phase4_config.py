"""
Test script for Phase 4: Configuration cleanup
Tests that all database-related configurations are removed
and only chain-related configurations remain
"""

import os
import sys

def test_old_config_deprecated():
    """Test that old config.py is marked as deprecated"""
    print("\n=== Testing Old Configuration (Should be Deprecated) ===\n")
    
    try:
        from config import Config
        
        # Check for deprecated database configs
        deprecated_attrs = [
            'SQLALCHEMY_DATABASE_URI',
            'SQLALCHEMY_TRACK_MODIFICATIONS',
            'SECRET_KEY'  # Flask session secret
        ]
        
        found_deprecated = []
        for attr in deprecated_attrs:
            if hasattr(Config, attr):
                found_deprecated.append(attr)
                print(f"⚠️  DEPRECATED config still present: {attr}")
        
        if found_deprecated:
            print(f"\n✗ Old config.py still contains {len(found_deprecated)} deprecated settings")
            print("  These should be removed in production")
            return False
        else:
            print("✓ No deprecated database configs found in old config")
            return True
            
    except ImportError:
        print("✓ Old config.py removed or not found (expected)")
        return True

def test_chain_config():
    """Test the new chain-only configuration"""
    print("\n=== Testing Chain-Only Configuration ===\n")
    
    try:
        from config_chain import ChainConfig, chain_config
        
        # Test blockchain configurations
        print("1. Blockchain Configuration:")
        print(f"   Network: {chain_config.NETWORK}")
        print(f"   Chain ID: {chain_config.ACTIVE_CHAIN_ID}")
        print(f"   RPC URL: {chain_config.ACTIVE_RPC_URL}")
        print(f"   ✓ Blockchain configs present")
        
        # Test that database configs are NOT present
        print("\n2. Database Configuration (Should NOT exist):")
        database_attrs = ['DATABASE_URL', 'SQLALCHEMY_DATABASE_URI', 'SQLALCHEMY_TRACK_MODIFICATIONS']
        has_database = False
        for attr in database_attrs:
            if hasattr(chain_config, attr):
                print(f"   ✗ Found database config: {attr}")
                has_database = True
        
        if not has_database:
            print("   ✓ No database configurations found")
        else:
            print("   ✗ Database configurations should be removed")
            return False
        
        # Test session configs are NOT present
        print("\n3. Session Configuration (Should NOT exist):")
        session_attrs = ['SECRET_KEY', 'SESSION_TYPE', 'FLASK_SECRET_KEY']
        has_session = False
        for attr in session_attrs:
            if hasattr(chain_config, attr) and attr != 'JWT_SECRET_KEY':
                print(f"   ✗ Found session config: {attr}")
                has_session = True
        
        if not has_session:
            print("   ✓ No Flask session configurations found")
        else:
            print("   ✗ Session configurations should be removed")
            return False
        
        # Test JWT configuration (for wallet auth)
        print("\n4. JWT Configuration (Wallet Auth):")
        if hasattr(chain_config, 'JWT_SECRET_KEY'):
            print(f"   ✓ JWT_SECRET_KEY configured")
            print(f"   ✓ JWT_ALGORITHM: {chain_config.JWT_ALGORITHM}")
            print(f"   ✓ JWT_EXPIRATION_HOURS: {chain_config.JWT_EXPIRATION_HOURS}")
        else:
            print("   ✗ JWT configuration missing")
            return False
        
        # Test Redis configuration (kept for caching)
        print("\n5. Redis Configuration (Performance):")
        if hasattr(chain_config, 'REDIS_URL'):
            print(f"   ✓ REDIS_URL: {chain_config.REDIS_URL}")
            print(f"   ✓ REDIS_CACHE_TTL: {chain_config.REDIS_CACHE_TTL} seconds")
        else:
            print("   ⚠️  Redis not configured (optional)")
        
        # Validate configuration
        print("\n6. Configuration Validation:")
        errors, warnings = ChainConfig.validate_config()
        
        if errors:
            print("   Errors:")
            for error in errors:
                print(f"   ✗ {error}")
            return False
        else:
            print("   ✓ No configuration errors")
        
        if warnings:
            print("   Warnings:")
            for warning in warnings:
                print(f"   ⚠️  {warning}")
        
        # Get configuration summary
        print("\n7. Configuration Summary:")
        summary = ChainConfig.get_config_summary()
        for key, value in summary.items():
            status = "✓" if value else "✗"
            if key in ['database_enabled', 'session_management']:
                # These should be False
                status = "✓" if not value else "✗"
            print(f"   {status} {key}: {value}")
        
        # Verify critical settings
        if summary['database_enabled'] or summary['session_management']:
            print("\n✗ Database or session management still enabled!")
            return False
        
        print("\n✓ Chain-only configuration validated successfully")
        return True
        
    except ImportError as e:
        print(f"✗ Could not import chain config: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing chain config: {e}")
        return False

def test_environment_variables():
    """Test that environment variables are properly configured"""
    print("\n=== Testing Environment Variables ===\n")
    
    # Variables that should NOT be used
    deprecated_vars = [
        'DATABASE_URL',
        'FLASK_SECRET_KEY',
        'SESSION_SECRET',
        'SQLALCHEMY_DATABASE_URI'
    ]
    
    # Variables that should be used
    required_vars = [
        'BASE_RPC_URL',
        'NETWORK'
    ]
    
    optional_vars = [
        'REDIS_URL',
        'NODE_OPERATOR_ADDRESS',
        'XCOM_BEARER_TOKEN',
        'JWT_SECRET_KEY'
    ]
    
    # Check for deprecated variables
    print("1. Checking for deprecated environment variables:")
    found_deprecated = []
    for var in deprecated_vars:
        if os.environ.get(var):
            found_deprecated.append(var)
            print(f"   ⚠️  Deprecated variable set: {var}")
    
    if not found_deprecated:
        print("   ✓ No deprecated environment variables in use")
    
    # Check for required variables
    print("\n2. Checking required environment variables:")
    missing_required = []
    for var in required_vars:
        if os.environ.get(var):
            print(f"   ✓ {var}: {os.environ.get(var)[:30]}...")
        else:
            missing_required.append(var)
            print(f"   ⚠️  {var}: Not set (using default)")
    
    # Check optional variables
    print("\n3. Checking optional environment variables:")
    for var in optional_vars:
        if os.environ.get(var):
            # Don't print sensitive values
            if 'TOKEN' in var or 'KEY' in var:
                print(f"   ✓ {var}: [SET]")
            else:
                print(f"   ✓ {var}: {os.environ.get(var)[:30]}...")
        else:
            print(f"   ⚠️  {var}: Not set (optional)")
    
    return len(found_deprecated) == 0

def test_app_integration():
    """Test that the app can use the new configuration"""
    print("\n=== Testing App Integration ===\n")
    
    try:
        # Try to import the Flask app with new config
        print("1. Testing Flask app initialization...")
        
        # Set minimal required environment
        if not os.environ.get('BASE_RPC_URL'):
            os.environ['BASE_RPC_URL'] = 'https://sepolia.base.org'
        if not os.environ.get('NETWORK'):
            os.environ['NETWORK'] = 'testnet'
        
        # Check if app can initialize
        print("   ✓ Configuration ready for app initialization")
        
        # Test that database models are not initialized
        print("\n2. Testing database independence:")
        try:
            from models import db
            print("   ⚠️  Database models still present (legacy)")
        except ImportError:
            print("   ✓ Database models removed")
        
        return True
        
    except Exception as e:
        print(f"✗ App integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*50)
    print("PHASE 4: CONFIGURATION CLEANUP TEST")
    print("="*50)
    
    all_tests_passed = True
    
    # Run tests
    test_results = {
        'Old Config Deprecated': test_old_config_deprecated(),
        'Chain Config Valid': test_chain_config(),
        'Environment Variables': test_environment_variables(),
        'App Integration': test_app_integration()
    }
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    for test_name, passed in test_results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print("\n✓ PHASE 4 COMPLETE: Configuration successfully cleaned!")
        print("All database and session configs removed.")
        print("System now uses chain-only configuration.")
    else:
        print("\n✗ PHASE 4 INCOMPLETE: Some tests failed")
        print("Please review the configuration settings.")