# Clockchain Node Operator

## Overview
This project is a Flask-based distributed node operator application for the Clockchain network, implementing a linguistic prediction market. Its core purpose is to enable users to bet on predicted linguistic outputs of public figures. Nodes engage in consensus mechanisms, oracle services, and blockchain validation. The system utilizes an immutable Synthetic Time Ledger, where all transactions and resolutions are recorded.

Key capabilities include:
- **Submissions**: Users predict that a specific actor will utter certain words within a defined time block, backing their predictions with a fee and a personal bet.
- **Bets**: A secondary market where users can bet on competing submissions for the same actors, with outcomes resolved by Levenshtein distance.
- **Resolution**: An oracle service validates source authenticity and measures the Levenshtein distance (stripping punctuation) between actual and predicted text within the specified timeframe.
- **Immutable Ledger**: The Synthetic Time Ledger ensures data immutability, with Time Sync services maintaining node synchronization without altering the ledger.

The project aims to create a robust and decentralized prediction market for linguistic data, leveraging blockchain technology for transparency and immutability.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Major Changes (August 2025)
- **Phase 1 Complete**: Backend transitioned to blockchain-first with database writes disabled
- **Phase 2 Complete**: Frontend fully integrated with Web3.js and MetaMask
- **Phase 3 Complete (August 5)**: Test infrastructure fully migrated to blockchain
  - Created blockchain test data generation tool (scripts/blockchain_test_data.py)
  - Created blockchain test data cleanup tool (scripts/clean_blockchain_test_data.py)
  - Updated test manager to use blockchain scripts
  - Removed all database test data files
- **Phase 4 Complete (August 5)**: Documentation and legacy code cleanup
  - Removed all legacy database-related files
  - Updated README.md for blockchain-only operations
  - Updated ENGINEERING.md to reflect current architecture
  - Eliminated all database setup instructions
- **Bittensor AI Integration (August 12)**: Added comprehensive Bittensor network support
  - Integrated TAO token economics for AI agent rewards
  - Added Yuma consensus scoring for performance tracking
  - Implemented AI transparency framework with 60% bonus rewards
  - Updated all documentation to include Bittensor integration details
  - Fixed CSS visibility issues on landing page (grey-on-black text)
- **Critical Logic Analysis (August 12)**: Identified fundamental platform flaw
  - Created LOGIC.md documenting centralized fee distribution issue
  - Platform fee (7%) currently goes to single owner address - contradicts "distributed" claim
  - Proposed distributed fee model: Oracles (2%), Nodes (1%), Creators (1%), Liquidity (2%), DAO (1%)
  - Documented AI agent financial tracking requirements and API improvements needed
- **Architecture**: System now operates in hybrid mode - new data on blockchain, historical data read-only from database
- **JavaScript Architecture**: Created modular Web3 integration (wallet.js, market-blockchain.js, etc.)
- **Documentation**: Updated ON-CHAIN-CHANGES.md to Production Readiness Plan, created LOGIC.md for mechanism analysis

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM (legacy, moving to blockchain-only).
- **Database**: PostgreSQL for production, SQLite for development (legacy, moving to blockchain-only).
- **Task Queue**: Celery, utilizing Redis as both broker and result backend.
- **Caching**: Redis for distributed caching and real-time data.
- **Time Management**: Custom Pacific Time synchronization service.
- **Blockchain**: BASE-exclusive integration.

### Frontend Architecture
- **Templating**: Jinja2 templates, styled with Bootstrap for responsive UI.
- **Interactivity**: Vanilla JavaScript with Chart.js for data visualization.
- **Styling**: Custom CSS for the admin dashboard and Bootstrap theming.
- **Real-time Updates**: WebSocket connections facilitate live data streaming.
- **Wallet Integration**: MetaMask and Coinbase Wallet with BASE network auto-switching.

### Core Services and Features
- **Consensus Service**: Manages node voting and network consensus (66% agreement required).
- **Oracle Service**: X.com integration with screenshot capture via Playwright for authenticity.
- **Blockchain Service**: BASE Sepolia/Mainnet transaction handling exclusively.
- **Ledger Service**: Manages entries in the immutable synthetic time ledger.
- **Time Sync Service**: Ensures node synchronization.
- **Text Analysis Service**: Calculates speech similarity using Levenshtein distance.
- **Node Communication**: WebSocket-based P2P network for real-time data exchange.
- **Production Monitoring**: Gas price tracking, oracle consensus monitoring, health checks.
- **Bittensor AI Integration**: Enables AI agents from Bittensor subnets to participate as validators/miners.
- **AI Transparency Framework**: Rewards transparent AI models with up to 60% bonus payouts.

### Smart Contracts (Deployed on BASE Sepolia)
- **PredictionMarket**: Core market functionality.
- **ClockchainOracle**: Legacy oracle system.
- **NodeRegistry**: Node operator management.
- **PayoutManager**: Automated payouts.
- **ActorRegistry**: On-chain actor registry.
- **EnhancedPredictionMarket**: All market, submission, and bet data on-chain.
- **DecentralizedOracle**: On-chain text analysis.
- **AdvancedMarkets**: Supports multi-choice, conditional, and range markets.
- **SecurityAudit**: Production security features like rate limiting and emergency controls.

### Data Models
Key data models include `NodeOperator`, `Actor`, `PredictionMarket`, `Submission`, `Bet`, `Transaction`, `OracleSubmission`, and `SyntheticTimeEntry`, all updated for BASE-exclusive operation.

### System Design Choices
- **UI/UX**: Dark theme with gradient accents, prioritizing technical clarity and an authentic blockchain aesthetic. Includes responsive design elements and real-time data displays.
- **Data Flow**: Market creation → submissions → betting → oracle resolution → payout distribution, all on BASE blockchain.
- **Background Tasks**: Contract monitoring, network reconciliation, consensus processing, production metrics collection.
- **Security**: Node-based authentication, RSA key pairs for digital signatures, robust input validation, and secure inter-node communication.
- **Deployment**: Gunicorn web server, Celery workers, Redis caching, production monitoring service.

## External Dependencies

### Core Libraries and Frameworks
- **Flask**: Web framework.
- **SQLAlchemy**: ORM for database interactions (legacy).
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
- **BASE Blockchain**: Exclusive blockchain platform (Coinbase L2).
- **BASE Sepolia**: Testnet for development and testing.
- **Web3.py**: For BASE blockchain interaction.
- **Smart Contracts**: Custom Solidity contracts deployed on BASE.

### Third-Party Services
- **X.com API**: Integrated as the primary oracle source for tweet data and screenshot proofs.