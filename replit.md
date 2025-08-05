# Clockchain Node Operator

## Overview

This project is a Flask-based distributed node operator application for the Clockchain network, implementing a linguistic prediction market. Its core purpose is to enable users to bet on predicted linguistic outputs of public figures. Nodes engage in consensus mechanisms, oracle services, and blockchain validation. The system utilizes an immutable Synthetic Time Ledger, where all transactions and resolutions are recorded.

Key capabilities include:
- **Submissions**: Users predict that a specific actor will utter certain words within a defined time block, backing their predictions with a fee and a personal bet.
- **Bets**: A secondary market where users can bet on competing submissions for the same actors, with outcomes resolved by Levenshtein distance, not binary results.
- **Resolution**: An oracle service validates source authenticity and measures the Levenshtein distance (stripping punctuation) between actual and predicted text within the specified timeframe.
- **Immutable Ledger**: The Synthetic Time Ledger ensures data immutability, with Time Sync services maintaining node synchronization without altering the ledger.

The project aims to create a robust and decentralized prediction market for linguistic data, leveraging blockchain technology for transparency and immutability.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM.
- **Database**: PostgreSQL for production, SQLite for development.
- **Task Queue**: Celery, utilizing Redis as both broker and result backend.
- **Caching**: Redis for distributed caching and real-time data.
- **Time Management**: Custom Pacific Time synchronization service.
- **Blockchain**: BASE-exclusive integration (no ETH/BTC support).

### Frontend Architecture
- **Templating**: Jinja2 templates, styled with Bootstrap for responsive UI.
- **Interactivity**: Vanilla JavaScript with Chart.js for data visualization.
- **Styling**: Custom CSS for the admin dashboard and Bootstrap theming.
- **Real-time Updates**: WebSocket connections facilitate live data streaming.
- **Wallet Integration**: MetaMask and Coinbase Wallet with BASE network auto-switching.

### Core Services and Features
- **Consensus Service**: Manages node voting and network consensus (66% agreement required).
- **Oracle Service**: X.com integration with screenshot capture via Playwright.
- **Blockchain Service**: BASE Sepolia/Mainnet transaction handling exclusively.
- **Ledger Service**: Manages entries in the immutable synthetic time ledger.
- **Time Sync Service**: Ensures node synchronization.
- **Text Analysis Service**: Calculates speech similarity using Levenshtein distance.
- **Node Communication**: WebSocket-based P2P network for real-time data exchange.
- **Production Monitoring**: Gas price tracking, oracle consensus monitoring, health checks.

### Smart Contracts (BASE Sepolia - All 14 Phases Deployed)
- **PredictionMarket**: `0xBca969b80D7Fb4b68c0529beEA19DB8Ecf96c5Ad` - Core market functionality
- **ClockchainOracle**: `0x9AA2aDbde623E019066cE604C81AE63E18d65Ec8` - Legacy oracle system
- **NodeRegistry**: `0xA69C842F335dfE1F69288a70054A34018282218d` - Node operator management
- **PayoutManager**: `0x88d399C949Ff2f1aaa8eA5a859Ae4d97c74f6871` - Automated payouts
- **ActorRegistry**: `0xC71CC19C5573C5E1E144829800cD0005D0eDB723` - On-chain actor registry
- **EnhancedPredictionMarket**: `0x6B67Cb0DaAf78f63BD11195Df0FD9FFe4361b93C` - All data on-chain
- **DecentralizedOracle**: `0x7EF22e27D44E3f4Cc2f133BB4ab2065D180be3C1` - On-chain text analysis
- **AdvancedMarkets**: `0x6143DfCEe9C4b38A37310058eCA9D2E509D5166B` - Advanced market types
- **SecurityAudit**: `0x0539ad4a63E76130d76a21163960906Eb47c1a9a` - Production security
- **Total deployment cost**: ~0.015 BASE (~$0.60 USD)

### Data Models
Key data models include `NodeOperator`, `Actor`, `PredictionMarket`, `Submission`, `Bet`, `Transaction`, `OracleSubmission`, and `SyntheticTimeEntry`, all updated for BASE-exclusive operation.

### System Design Choices
- **UI/UX**: Dark theme with gradient accents, prioritizing technical clarity and an authentic blockchain aesthetic. Includes responsive design elements and real-time data displays.
- **Data Flow**: Market creation → submissions → betting → oracle resolution → payout distribution, all on BASE blockchain.
- **Background Tasks**: Contract monitoring, network reconciliation, consensus processing, production metrics collection.
- **Security**: Node-based authentication, RSA key pairs for digital signatures, robust input validation, and secure inter-node communication.
- **Deployment**: Gunicorn web server, Celery workers, PostgreSQL database, Redis caching, production monitoring service.

## External Dependencies

### Core Libraries and Frameworks
- **Flask**: Web framework.
- **SQLAlchemy**: ORM for database interactions.
- **Celery**: Distributed task queue.
- **Redis**: In-memory data store for caching and messaging.
- **Web3**: Python library for interacting with Ethereum blockchains.
- **python-Levenshtein**: For efficient Levenshtein distance calculations.
- **Cryptography**: For digital signatures and encryption.

### Frontend Libraries
- **Bootstrap**: UI framework.
- **Chart.js**: For data visualization.
- **Font Awesome**: Icon library.
- **WebSocket**: For real-time communication in the browser.

### Blockchain Integration
- **BASE Blockchain**: Exclusive blockchain platform (Coinbase L2)
- **BASE Sepolia**: Testnet for development and testing
- **Web3.py**: For BASE blockchain interaction
- **Smart Contracts**: Custom Solidity contracts deployed on BASE

### Third-Party Services
- **X.com API**: Integrated as the primary oracle source for tweet data and screenshot proofs.

## Project Documentation

### Documentation Structure
- **README.md**: Project overview, current status, and deployed contract addresses
- **ENGINEERING.md**: Technical implementation details, architecture, and completed phases
- **CRYPTO_PLAN.md**: Remaining work plan (X.com integration and production launch)
- **TEST_DATA_GUIDE.md**: Comprehensive test data generation and blockchain transaction testing guide
- **TEST_WALLET_SETUP.md**: Test wallet configuration for BASE Sepolia

### Test Infrastructure
- **Test Manager Interface**: Visual UI at `/test_manager` for creating and managing test scenarios
- **E2E Test Suite**: Automated testing with `test_e2e_runner.py`
- **Data Generator**: Realistic test data via `scripts/generate_realistic_data.py`
- **Network Transaction Testing**: Full blockchain transaction propagation plan (see TEST_DATA_GUIDE.md)

## Recent Changes

### August 5, 2025 - Phases 9-14 Successfully Deployed to BASE Sepolia
- **Phase 9 - ActorRegistry**: Deployed at 0xC71CC19C5573C5E1E144829800cD0005D0eDB723
- **Phase 10 - EnhancedPredictionMarket**: Deployed at 0x6B67Cb0DaAf78f63BD11195Df0FD9FFe4361b93C
- **Phase 11 - DecentralizedOracle**: Deployed at 0x7EF22e27D44E3f4Cc2f133BB4ab2065D180be3C1
- **Phase 13 - AdvancedMarkets**: Deployed at 0x6143DfCEe9C4b38A37310058eCA9D2E509D5166B
- **Phase 14 - SecurityAudit**: Deployed at 0x0539ad4a63E76130d76a21163960906Eb47c1a9a
- **Fixed Issues**: Updated OpenZeppelin v5 import paths and ethers v6 deployment scripts
- **Deployment Scripts**: Created deploy-phase9-10.js, deploy-phase11-12.js, and deploy-phase13-14.js

### August 5, 2025 - Phases 11-14 Complete Implementation
- **Phase 11 - Decentralized Oracle System**: 
  - Created DecentralizedOracle.sol with on-chain Levenshtein distance calculation
  - Multi-validator consensus mechanism with configurable thresholds
  - IPFS integration for screenshot storage
  - Backend service decentralized_oracle.py for automated validation
- **Phase 12 - PostgreSQL Elimination**: 
  - Created blockchain_only_data.py for direct blockchain data queries
  - Implemented p2p_communication.py for WebRTC-based node communication
  - Event-driven architecture with local caching
  - Complete removal of database dependencies
- **Phase 13 - Advanced Markets**:
  - Created AdvancedMarkets.sol supporting multi-choice, conditional, and range markets
  - Implemented distributed_storage.py for comprehensive IPFS integration
  - Added advanced_markets.py service for complex market operations
  - Built user reputation system for trust scoring
- **Phase 14 - Security & Production**:
  - Created SecurityAudit.sol with rate limiting and emergency controls
  - Implemented security_audit.py for real-time threat monitoring
  - Added blacklisting, transaction limits, and suspicious activity detection
  - System now production-ready with comprehensive security features
- **Deployment Scripts**: Created deploy-phase11-12.js and deploy-phase13-14.js
- **Test Infrastructure**: Added test_phase11_12.py and test_phase13_14.py

### August 5, 2025 - Phase 9 & 10 Implementation
- **Phase 9 - On-Chain Actor Registry**: Implemented ActorRegistry.sol with decentralized approval mechanism requiring 3+ node operator votes
- **Phase 10 - Fully On-Chain Markets**: Created EnhancedPredictionMarket.sol to store all market, submission, and bet data on-chain
- **Backend Services**: Added actor_registry.py and blockchain_enhanced.py for on-chain operations
- **Migration Scripts**: Created deploy-phase9-10.js and migrate-actors.js for smooth transition
- **Removed PostgreSQL Dependencies**: Moved from hybrid storage to fully blockchain-based data management
- **Fixed Service Errors**: Resolved all LSP diagnostic issues in actor registry and enhanced blockchain services

### January 31, 2025 - X.com Actor System Implementation
- **Migrated Actor System**: Transitioned from wallet-based to X.com username-based actor identification
- **Database Schema Update**: Added x_username, display_name, bio, verified, follower_count fields to Actor model
- **Legacy Field Handling**: Made old fields (name, description, wallet_address) nullable for compatibility
- **Test Data Creation**: Generated 8 test actors with real X.com handles (@elonmusk, @taylorswift13, etc.)
- **UI Updates**: Modified templates to display @username format with verification badges
- **Documentation Updates**: Updated README.md, ENGINEERING.md, and CRYPTO_PLAN.md with new architecture
- **Launch Guide**: Created comprehensive LAUNCH.md for production deployment on BASE mainnet

### January 31, 2025 - Documentation Reorganization
- Moved completed phases (1-7) from CRYPTO_PLAN.md to ENGINEERING.md
- Updated README.md with correct BASE Sepolia contract addresses
- Created simplified CRYPTO_PLAN.md focusing on remaining X.com integration work
- Fixed currency references throughout codebase (now BASE-exclusive)
- Created TEST_DATA_GUIDE.md with comprehensive testing documentation
- Added complete blockchain transaction testing plan for node network propagation

### Project Status
- **Completed**: 
  - Phases 1-7: Smart contracts deployed, backend/frontend integration, production monitoring
  - Phase 8: X.com actor system migration
  - Phase 9: On-Chain Actor Registry with decentralized approval
  - Phase 10: Fully On-Chain Markets (EnhancedPredictionMarket)
  - Phase 11: Decentralized Oracle System with on-chain Levenshtein calculation
  - Phase 12: PostgreSQL Elimination - fully blockchain-based architecture
  - Phase 13: Advanced Markets - multi-choice, conditional, range predictions, IPFS storage
  - Phase 14: Security & Production - rate limiting, emergency controls, comprehensive monitoring
- **Ready for Production**: All 14 phases complete, system fully decentralized
- **Remaining**: Production X.com API credentials, mainnet deployment, third-party security audit
- **Basescan**: For contract verification and transaction exploration on the BASE blockchain.

## Recent Changes

### Secondary Node Implementation (July 31, 2025)
- **Created Simple Secondary Node System**:
  - clockchain_node_monolith.py - Lightweight single-file node implementation
  - Automatic wallet generation for node identity
  - WebSocket connection for inter-node communication
  - Heartbeat mechanism to maintain active status
  - Consensus participation (simplified voting)
- **Setup Scripts**:
  - python_setup.sh - Automated setup with wallet generation
  - python_test.sh - Comprehensive testing of node setup
  - python_run.sh - Simple node execution
  - Options for venv, requirements generation, custom installation
- **Node API Integration**:
  - Created routes/node_api.py with endpoints for node operations
  - /api/health - Health check endpoint
  - /api/nodes/register - Node registration
  - /api/nodes/heartbeat - Heartbeat reception
  - /api/nodes/<address> - Node status checking
  - /api/nodes - List all registered nodes
- **Environment Configuration**:
  - Automatic .env.node generation with all required variables
  - NODE_ID, NODE_ADDRESS, NODE_PRIVATE_KEY auto-generated
  - Contract addresses pre-configured for BASE Sepolia
  - Database URL inherited from main application
- **Documentation**:
  - Created SECONDARY_NODE_README.md with setup instructions
  - Simple quick start guide
  - Troubleshooting section
  - Security notes for wallet management