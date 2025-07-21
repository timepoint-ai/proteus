from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class NodeOperator(db.Model):
    __tablename__ = 'node_operators'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id = db.Column(db.String(256), unique=True, nullable=False)
    public_key = db.Column(db.Text, nullable=False)
    node_address = db.Column(db.String(512), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, inactive, pending
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    votes_cast = db.relationship('NodeVote', foreign_keys='NodeVote.voter_id', backref='voter')
    votes_received = db.relationship('NodeVote', foreign_keys='NodeVote.candidate_id', backref='candidate')

class Actor(db.Model):
    __tablename__ = 'actors'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    wallet_address = db.Column(db.String(128))
    is_unknown = db.Column(db.Boolean, default=False)
    approval_votes = db.Column(db.Integer, default=0)
    rejection_votes = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    markets = db.relationship('PredictionMarket', backref='actor')
    actor_votes = db.relationship('ActorVote', backref='actor')

class PredictionMarket(db.Model):
    __tablename__ = 'prediction_markets'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('actors.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    oracle_wallets = db.Column(db.Text, nullable=False)  # JSON array of wallet addresses
    status = db.Column(db.String(20), default='active')  # active, expired, validating, resolved, cancelled
    resolution_text = db.Column(db.Text)
    winning_submission_id = db.Column(UUID(as_uuid=True))  # Set after resolution
    resolution_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('Submission', backref='market', foreign_keys='Submission.market_id')
    oracle_submissions = db.relationship('OracleSubmission', backref='market')

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    market_id = db.Column(UUID(as_uuid=True), db.ForeignKey('prediction_markets.id'), nullable=False)
    creator_wallet = db.Column(db.String(128), nullable=False)
    predicted_text = db.Column(db.Text)  # Nullable for null submissions
    submission_type = db.Column(db.String(20), nullable=False)  # original, competitor, null
    initial_stake_amount = db.Column(db.Numeric(20, 8), nullable=False)
    currency = db.Column(db.String(10), nullable=False)  # ETH, BTC, TAO
    transaction_hash = db.Column(db.String(128), nullable=False)
    levenshtein_distance = db.Column(db.Integer)
    is_winner = db.Column(db.Boolean, default=False)
    
    # AI Agent and Transparency Fields
    is_ai_agent = db.Column(db.Boolean, default=False)
    ai_agent_id = db.Column(db.String(256))  # Bittensor UID or custom agent ID
    transparency_level = db.Column(db.Integer, default=0)  # 0-4 based on modules used
    total_reward_bonus = db.Column(db.Numeric(5, 4), default=0)  # Total bonus percentage (0.00 to 0.95)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bets = db.relationship('Bet', backref='submission')
    verification_modules = db.relationship('VerificationModule', backref='submission', cascade='all, delete-orphan')

class Bet(db.Model):
    __tablename__ = 'bets'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = db.Column(UUID(as_uuid=True), db.ForeignKey('submissions.id'), nullable=False)
    bettor_wallet = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Numeric(20, 8), nullable=False)
    currency = db.Column(db.String(10), nullable=False)  # ETH, BTC
    transaction_hash = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, won, lost, refunded
    payout_amount = db.Column(db.Numeric(20, 8))
    payout_transaction_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Renamed from Stake - no longer needed
# Stakes are now Bets on Submissions

class OracleSubmission(db.Model):
    __tablename__ = 'oracle_submissions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    market_id = db.Column(UUID(as_uuid=True), db.ForeignKey('prediction_markets.id'), nullable=False)
    oracle_wallet = db.Column(db.String(128), nullable=False)
    submitted_text = db.Column(db.Text)  # Nullable for null oracle submission
    signature = db.Column(db.Text, nullable=False)
    votes_for = db.Column(db.Integer, default=0)
    votes_against = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, consensus, rejected
    is_consensus = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    votes = db.relationship('OracleVote', backref='submission')

class OracleVote(db.Model):
    __tablename__ = 'oracle_votes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = db.Column(UUID(as_uuid=True), db.ForeignKey('oracle_submissions.id'), nullable=False)
    voter_wallet = db.Column(db.String(128), nullable=False)
    vote = db.Column(db.String(10), nullable=False)  # 'for' or 'against'
    signature = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NodeVote(db.Model):
    __tablename__ = 'node_votes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('node_operators.id'), nullable=False)
    candidate_id = db.Column(UUID(as_uuid=True), db.ForeignKey('node_operators.id'), nullable=False)
    vote = db.Column(db.String(10), nullable=False)  # 'approve' or 'reject'
    signature = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ActorVote(db.Model):
    __tablename__ = 'actor_votes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('actors.id'), nullable=False)
    voter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('node_operators.id'), nullable=False)
    vote = db.Column(db.String(10), nullable=False)  # 'approve' or 'reject'
    signature = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_hash = db.Column(db.String(128), unique=True, nullable=False)
    from_address = db.Column(db.String(128), nullable=False)
    to_address = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Numeric(20, 8), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # stake, payout, fee, refund
    related_market_id = db.Column(UUID(as_uuid=True), db.ForeignKey('prediction_markets.id'))
    related_submission_id = db.Column(UUID(as_uuid=True), db.ForeignKey('submissions.id'))
    related_bet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('bets.id'))
    platform_fee = db.Column(db.Numeric(20, 8), default=0)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, failed
    block_number = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SyntheticTimeEntry(db.Model):
    __tablename__ = 'synthetic_time_entries'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp_ms = db.Column(db.BigInteger, nullable=False)  # Pacific Time in milliseconds
    entry_type = db.Column(db.String(20), nullable=False)  # market_created, submission_created, bet_placed, resolution, etc.
    entry_data = db.Column(db.Text, nullable=False)  # JSON data
    node_id = db.Column(UUID(as_uuid=True), db.ForeignKey('node_operators.id'), nullable=False)
    signature = db.Column(db.Text, nullable=False)
    reconciled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NetworkMetrics(db.Model):
    __tablename__ = 'network_metrics'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    active_nodes = db.Column(db.Integer, default=0)
    total_markets = db.Column(db.Integer, default=0)
    total_submissions = db.Column(db.Integer, default=0)
    total_bets = db.Column(db.Integer, default=0)
    total_volume_eth = db.Column(db.Numeric(20, 8), default=0)
    total_volume_btc = db.Column(db.Numeric(20, 8), default=0)
    platform_fees_eth = db.Column(db.Numeric(20, 8), default=0)
    platform_fees_btc = db.Column(db.Numeric(20, 8), default=0)
    consensus_accuracy = db.Column(db.Float, default=0.0)

# AI Agent Transparency Models

class VerificationModule(db.Model):
    """Tracks which verification modules an AI agent has submitted for a prediction"""
    __tablename__ = 'verification_modules'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = db.Column(UUID(as_uuid=True), db.ForeignKey('submissions.id'), nullable=False)
    module_type = db.Column(db.String(50), nullable=False)  # open_source, architecture, reasoning, audit
    
    # Module-specific data storage
    ipfs_hash = db.Column(db.String(256))  # For open source code
    blockchain_reference = db.Column(db.String(256))  # For on-chain storage
    model_architecture = db.Column(db.Text)  # JSON describing architecture
    training_data_hash = db.Column(db.String(256))  # Hash of training data
    reasoning_trace = db.Column(db.Text)  # Detailed reasoning process
    computational_proof = db.Column(db.Text)  # Cryptographic proof
    audit_report_hash = db.Column(db.String(256))  # Third-party audit reference
    
    # Verification status
    is_verified = db.Column(db.Boolean, default=False)
    verification_timestamp = db.Column(db.DateTime)
    verification_details = db.Column(db.Text)  # JSON with verification results
    
    # Reward bonus for this module
    reward_bonus = db.Column(db.Numeric(5, 4), default=0)  # Bonus percentage (e.g., 0.15 for 15%)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BittensorIntegration(db.Model):
    """Manages Bittensor TAO integration for AI agents"""
    __tablename__ = 'bittensor_integrations'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ai_agent_id = db.Column(db.String(256), unique=True, nullable=False)  # Bittensor UID
    subnet_id = db.Column(db.Integer)  # Bittensor subnet (1-50+)
    neuron_type = db.Column(db.String(20))  # validator or miner
    hotkey_address = db.Column(db.String(256), nullable=False)
    coldkey_address = db.Column(db.String(256))
    
    # TAO staking and rewards
    tao_staked = db.Column(db.Numeric(20, 8), default=0)
    tao_earned = db.Column(db.Numeric(20, 8), default=0)
    
    # Performance metrics
    yuma_score = db.Column(db.Float)  # Yuma consensus score
    trust_score = db.Column(db.Float)  # Network trust score
    total_predictions = db.Column(db.Integer, default=0)
    successful_predictions = db.Column(db.Integer, default=0)
    
    # Integration status
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AIAgentProfile(db.Model):
    """Extended profile for AI agents with transparency metrics"""
    __tablename__ = 'ai_agent_profiles'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = db.Column(db.String(256), unique=True, nullable=False)
    agent_name = db.Column(db.String(256))
    organization = db.Column(db.String(256))
    
    # Transparency commitments
    transparency_level = db.Column(db.Integer, default=0)  # 0-4 based on modules
    open_source_commitment = db.Column(db.Boolean, default=False)
    architecture_disclosure = db.Column(db.Boolean, default=False)
    reasoning_transparency = db.Column(db.Boolean, default=False)
    audit_participation = db.Column(db.Boolean, default=False)
    
    # Performance and reputation
    total_submissions = db.Column(db.Integer, default=0)
    winning_submissions = db.Column(db.Integer, default=0)
    average_accuracy = db.Column(db.Float, default=0.0)
    reputation_score = db.Column(db.Float, default=0.0)
    
    # Economic metrics
    total_staked = db.Column(db.Numeric(20, 8), default=0)
    total_earned = db.Column(db.Numeric(20, 8), default=0)
    total_bonuses = db.Column(db.Numeric(20, 8), default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TransparencyAudit(db.Model):
    """Third-party audits of AI agent transparency claims"""
    __tablename__ = 'transparency_audits'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = db.Column(db.String(256), nullable=False)
    auditor_name = db.Column(db.String(256), nullable=False)
    auditor_wallet = db.Column(db.String(128))
    
    # Audit details
    audit_type = db.Column(db.String(50))  # code_review, architecture_validation, etc.
    audit_scope = db.Column(db.Text)  # What was audited
    audit_methodology = db.Column(db.Text)  # How it was audited
    
    # Results
    audit_passed = db.Column(db.Boolean, default=False)
    findings = db.Column(db.Text)  # JSON with detailed findings
    recommendations = db.Column(db.Text)
    
    # Verification
    audit_hash = db.Column(db.String(256))  # Hash of full audit report
    signature = db.Column(db.Text)  # Auditor's signature
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # When audit validity expires

