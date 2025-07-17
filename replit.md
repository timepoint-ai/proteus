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

## Recent Changes (July 17, 2025)

### Clockchain Timeline Enhancement
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

### Comprehensive Documentation (July 17, 2025)
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