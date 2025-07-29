# Clockchain Node Operator

## Overview

This is a Flask-based distributed node operator application for the Clockchain network. The system implements a linguistic prediction market where nodes participate in consensus mechanisms, oracle services, and blockchain validation.

### Key Concepts:
- **Submissions**: Initial predictions where users bet that a certain actor will say certain words in a specific time block. These are transactions that must pay fees to node operators and require the initial user to make a bet on their own submission.
- **Bets**: Secondary market where other users express confidence in competing submissions for the same actors. These compare Levenshtein distances, not binary outcomes.
- **Resolution**: Oracle validates the source and uses Levenshtein distance (stripping punctuation) to measure how close actual text is to predicted text within the timeframe.
- **Immutable Ledger**: The Synthetic Time Ledger is immutable once started - Time Sync does not adjust the ledger, it only ensures nodes are synchronized.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Flask Application**: Main web framework with SQLAlchemy ORM
- **Database**: SQLite with PostgreSQL support via SQLAlchemy
- **Task Queue**: Celery with Redis as broker and result backend
- **Caching**: Redis for distributed caching and real-time communication
- **Time Management**: Custom Pacific Time synchronization service

### Frontend Architecture
- **Templates**: Jinja2 templates with Bootstrap for responsive UI
- **JavaScript**: Vanilla JS with Chart.js for data visualization
- **CSS**: Custom admin dashboard styling with Bootstrap theming
- **Real-time Updates**: WebSocket connections for live data

## Key Components

### Core Services
1. **Consensus Service**: Manages node voting and network consensus
2. **Oracle Service**: Validates source authenticity and performs Levenshtein analysis on submitted texts
3. **Blockchain Service**: Validates ETH/BTC transactions for submissions and bets
4. **Ledger Service**: Manages immutable synthetic time ledger entries
5. **Time Sync Service**: Ensures node synchronization (does not modify ledger)
6. **Text Analysis Service**: Calculates speech similarity using Levenshtein distance (punctuation stripped)
7. **Node Communication**: WebSocket-based inter-node communication

### Data Models
- **NodeOperator**: Network node management
- **Actor**: Public figures for speech prediction
- **Bet**: Prediction market bets
- **Stake**: User stakes in betting markets
- **Transaction**: Blockchain transaction records
- **OracleSubmission**: Oracle data submissions
- **SyntheticTimeEntry**: Time ledger entries

### Background Tasks
- **Network Reconciliation**: Periodic data synchronization
- **Consensus Processing**: Node proposal handling
- **Time Ledger Sync**: Distributed time synchronization
- **Oracle Processing**: Oracle submission validation

## Data Flow

1. **Node Registration**: New nodes register and undergo consensus voting
2. **Actor Management**: Public figures are added and voted on by nodes
3. **Submission Creation**: Users submit predictions (betting that actor will say specific text in time window)
4. **Bet Placement**: Other users place bets on competing submissions based on confidence
5. **Oracle Validation**: Oracles validate actual speech source and perform Levenshtein analysis
6. **Consensus Validation**: Network validates oracle submissions through voting
7. **Automatic Resolution**: Submissions resolve based on lowest Levenshtein distance within timeframe
8. **Transaction Recording**: All actions recorded in immutable synthetic time ledger

## External Dependencies

### Core Dependencies
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM with PostgreSQL/SQLite support
- **Celery**: Distributed task queue system
- **Redis**: Message broker and caching layer
- **Web3**: Ethereum blockchain interaction
- **Levenshtein**: Text similarity calculations
- **Cryptography**: Digital signatures and encryption

### Frontend Dependencies
- **Bootstrap**: UI framework with dark theme support
- **Chart.js**: Data visualization and metrics
- **Font Awesome**: Icon library
- **WebSocket**: Real-time communication

### Blockchain Integration
- **Ethereum**: ETH transaction validation via Web3
- **Bitcoin**: BTC transaction validation via REST API
- **Infura**: Ethereum RPC provider support

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database with local Redis
- **Production**: PostgreSQL with distributed Redis cluster
- **Docker**: Containerized deployment support
- **Environment Variables**: Secure configuration management

### Service Components
- **Web Server**: Flask application with Gunicorn
- **Worker Processes**: Celery workers for background tasks
- **Database**: PostgreSQL with connection pooling
- **Cache Layer**: Redis cluster for distributed caching
- **Load Balancer**: Nginx for request distribution

### Monitoring and Logging
- **Logging**: Structured logging with multiple levels
- **Health Checks**: API endpoints for service monitoring
- **Metrics**: Network statistics and performance tracking
- **Admin Dashboard**: Web-based node management interface

### Security Considerations
- **Authentication**: Node-based authentication system
- **Encryption**: RSA key pairs for message signing
- **Validation**: Input validation and sanitization
- **Network Security**: Secure inter-node communication

The system is designed to be highly distributed with fault tolerance, automatic reconciliation, and real-time consensus mechanisms for managing linguistic prediction markets across a network of nodes.

## Recent Changes

### Data Integrity & Documentation Updates (July 29, 2025)
- **Fixed Oracle Service**: Resolved UUID handling errors and created new /oracles pages outside admin
- **Enhanced Status Logic**: All status elements now display real database-calculated values, not hardcoded placeholders
  - Transaction statuses pulled from actual blockchain confirmations
  - Submission winners/losers determined by real Levenshtein distance calculations
  - Market statuses (active/expired/validating/resolved) computed from timestamps and oracle data
- **Created Realistic Test Data Generator**: Added `/generate/realistic` route
  - Generates actors, markets, and transactions with proper status workflows
  - Creates markets in various states with complete lifecycles
  - Simulates real Levenshtein distance calculations and oracle consensus
  - Proper foreign key relationships and realistic blockchain transactions
- **Updated Documentation**: Comprehensive updates to README.md, ENGINEERING.md, and /docs page
  - Added Data Integrity sections emphasizing real-time calculations
  - Updated schema documentation to reflect PredictionMarket → Submission → Bet structure
  - Documented realistic test data generator functionality

### Actors Pages and Pagination Implementation (July 28, 2025)
- **Created Actors Section**: Added new `/actors` routes to display registered actors
  - List view at `/actors` showing all actors with their status and market statistics
  - Individual actor detail pages at `/actors/<actor_id>` with comprehensive market history
  - Shows active markets, past markets, and total betting volume per actor
- **Implemented Full Pagination System**: Added "Load More" pagination across all Clockchain views
  - Created separate API blueprint (clockchain_api.py) for AJAX pagination endpoints
  - Paginated endpoints for all markets, resolved markets, and active markets
  - 10 entries loaded per request with "Load More" button functionality
  - Removed old time range controls in favor of streamlined pagination
- **Navigation Updates**: Added "Actors" link to main navigation between Markets and Oracles
- **Template Updates**: Enhanced timeline and submission templates to support new pagination structure

### Marketing Landing Page and Site Restructure (July 23, 2025)
- **Created New Marketing Landing Page**: Professional blockchain-style landing page at root URL ('/')
  - Demo banner indicating it's not a live site
  - Email capture form with database storage (EmailCapture model)
  - Comprehensive infographic explaining how Clockchain works
  - Sections covering API documentation and status workflow
  - Links to documentation page and demo
  - Custom Clockchain SVG logo in header
  - Authentic blockchain community design - technical, not splashy
  - Philosophical explanation of prediction market power with real-world examples
- **Route Restructuring**: 
  - Root '/' now serves marketing landing page instead of redirecting to admin
  - Admin dashboard moved to '/dashboard' route
  - Created comprehensive documentation page at '/docs'
  - Demo button redirects to Clockchain timeline view
- **New Models**: Added EmailCapture model for storing email signups from landing page
- **Design Philosophy**: Focused on authentic blockchain aesthetics with gradient accents, dark theme, and technical clarity

### Test Transaction Generator Implementation (July 21, 2025)
- **New Feature**: Added comprehensive test transaction generator for end-to-end blockchain testing
- **Management Dashboard**: Created `/test_transactions` dashboard for managing test sessions
- **Test Scenarios**: Implemented 3 pre-built scenarios with realistic actors and predictions:
  - Elon Musk tweet prediction (10-minute window)
  - Donald Trump Truth Social post (10-minute window)
  - Taylor Swift album announcement (15-minute window)
- **Mock Mode**: "Mock then actually push" strategy to prevent broken blockchain transactions
- **Complete Lifecycle Testing**:
  - Market creation with oracle configuration
  - Multiple submission creation (original and competitors)
  - Bet placement on submissions
  - Time-based market expiration
  - Oracle consensus submission
  - Levenshtein-based market resolution
  - Reward distribution and ledger reconciliation
- **Session Management**: Real-time session tracking with transaction logs and progress indicators
- **Wallet Configuration**: Added guide for configuring test wallets via Replit Secrets
- **Future Integration**: Prepared for real ETH/BTC wallet integration when configured

### AI Agent API Implementation (July 21, 2025)
- **New Feature**: Added rate-limited API for AI agents to create submissions in prediction markets
- **API Endpoints**:
  - `/ai_agent/v1/health` - Health check endpoint
  - `/ai_agent/v1/markets` - Get active markets accepting submissions
  - `/ai_agent/v1/markets/{id}/submissions` - Get submissions for a market
  - `/ai_agent/v1/submissions` - Create new submissions (original/competitor/null)
  - `/ai_agent/v1/calculate_fees` - Calculate required fees for submissions
- **Rate Limiting**: Implemented Flask-Limiter with 10 requests/minute for submission creation
- **Platform Fee**: Updated to use PLATFORM_FEE environment variable (7% default)
- **Documentation**: Created comprehensive API documentation at `/ai_agent/docs`
- **Security**: Wallet signature verification for all submissions
- **Integration**: AI agents must pay initial stake + platform fee (includes mining costs)

### Complete Schema Redesign to Competitive Submission Architecture (July 21, 2025)
- **Major Architecture Change**: Migrated from Bet→Stake model to PredictionMarket→Submission→Bet model
- **New Data Model Structure**:
  - PredictionMarket: Container for all predictions about an actor in a time window
  - Submission: Individual predictions (original, competitor, or null) within a market
  - Bet: Individual wagers placed on specific submissions
- **Text Analysis Updates**: Preserved X.com-compatible formatting (punctuation, spacing, capitalization)
- **Service Migration**: Updated all services (oracle_v2.py, bet_resolution_v2.py) to work with new schema
- **Route Updates**: Changed admin routes from /bets to /markets, updated all templates
- **Database Recreation**: Dropped old tables and created new schema with proper foreign key relationships
- **Test Data Generation**: Created new test_data_new.py that generates competitive submission scenarios
- **Clockchain Updates**: Modified timeline view to display markets with multiple submissions
- **Navigation Updates**: Changed UI from "Bets" to "Markets" throughout application

### Status Workflow Redesign (July 21, 2025)
- **Fixed critical status logic error**: Resolved bets can no longer have pending transactions
- **Implemented comprehensive status workflow**: 
  - Bets: active → expired → validating → resolved
  - Stakes: pending → confirmed → won/lost/refunded
  - Transactions: pending → confirmed/failed
  - Oracle Submissions: pending → consensus/rejected
- **Created BetResolutionService**: Handles proper status transitions and payout processing
- **Updated data models**: Added status fields to Stakes and OracleSubmissions
- **Created test_data_v2**: New test data generation that follows proper status workflow
- **Documented new workflow**: Created STATUS_WORKFLOW.md with complete specification

### Critical Oracle Timing Fix (July 18, 2025)
- **Fixed foundational logic error**: Oracle submissions were previously allowed before bet end_time
- **Implemented strict time validation**: Oracle submissions now only accepted AFTER bet's end_time has passed
- **Added TimeConsensusService**: New distributed time synchronization mechanism across nodes
- **Updated timeline UI**: Shows oracle submission eligibility status and time until oracle is allowed
- **Added background task**: Time consensus synchronization runs every 30 seconds
- **Enhanced documentation**: Updated README and ENGINEERING docs to emphasize temporal integrity requirement

### July 17, 2025 Changes

#### Clockchain Timeline Enhancement
- Replaced "Time Sync" navigation with "Clockchain" 
- Transformed timeline from metadata view to content-focused display showing:
  - Actor names and predicted statements prominently
  - Time windows for each prediction
  - Total bet volumes and competing submission counts
  - Links to detailed submission pages
- Created individual submission detail pages at `/clockchain/submission/<id>`
- Extended default timeline range to 1440 hours (60 days) with maximum range up to 10,000,000 hours
- Added performance optimization limiting records to 200 max with indicators when more data exists
- Added convenient time range presets (1 day, 1 week, 1 month, 2 months, 1 year, 5 years)

#### Comprehensive Documentation
- Created detailed README.md with user-focused documentation including:
  - Clear project overview and key features
  - Quick start guide with installation steps
  - Usage instructions for admin dashboard and timeline
  - Configuration options and deployment guide
  - Troubleshooting section
- Created extensive ENGINEERING.md with developer-focused documentation including:
  - Complete architecture overview with visual diagrams
  - Detailed system design principles
  - In-depth component and service descriptions
  - Consensus mechanism and text analysis algorithm details
  - Security architecture and performance optimization strategies
  - Testing, deployment, and monitoring guidelines
  - Development workflow and future enhancements