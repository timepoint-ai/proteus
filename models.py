import uuid
from datetime import datetime, timezone
from app import db
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import UUID
import json

class NodeOperator(db.Model):
    __tablename__ = 'node_operators'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id = db.Column(db.String(128), unique=True, nullable=False)
    public_key = db.Column(db.Text, nullable=False)
    node_address = db.Column(db.String(256), nullable=False)
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
    bets = db.relationship('Bet', backref='actor')
    actor_votes = db.relationship('ActorVote', backref='actor')

class Bet(db.Model):
    __tablename__ = 'bets'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_wallet = db.Column(db.String(128), nullable=False)
    actor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('actors.id'), nullable=False)
    predicted_text = db.Column(db.Text, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    oracle_wallets = db.Column(db.Text, nullable=False)  # JSON array of wallet addresses
    initial_stake_amount = db.Column(db.Numeric(20, 8), nullable=False)
    currency = db.Column(db.String(10), nullable=False)  # ETH, BTC
    transaction_hash = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, resolved, cancelled
    resolution_text = db.Column(db.Text)
    levenshtein_distance = db.Column(db.Integer)
    resolution_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stakes = db.relationship('Stake', backref='bet')
    oracle_submissions = db.relationship('OracleSubmission', backref='bet')

class Stake(db.Model):
    __tablename__ = 'stakes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('bets.id'), nullable=False)
    staker_wallet = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Numeric(20, 8), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    transaction_hash = db.Column(db.String(128), nullable=False)
    position = db.Column(db.String(10), nullable=False)  # 'for' or 'against'
    payout_amount = db.Column(db.Numeric(20, 8))
    payout_transaction_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OracleSubmission(db.Model):
    __tablename__ = 'oracle_submissions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('bets.id'), nullable=False)
    oracle_wallet = db.Column(db.String(128), nullable=False)
    submitted_text = db.Column(db.Text, nullable=False)
    signature = db.Column(db.Text, nullable=False)
    votes_for = db.Column(db.Integer, default=0)
    votes_against = db.Column(db.Integer, default=0)
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
    transaction_type = db.Column(db.String(20), nullable=False)  # stake, payout, fee
    related_bet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('bets.id'))
    platform_fee = db.Column(db.Numeric(20, 8), default=0)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, failed
    block_number = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SyntheticTimeEntry(db.Model):
    __tablename__ = 'synthetic_time_entries'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp_ms = db.Column(db.BigInteger, nullable=False)  # Pacific Time in milliseconds
    entry_type = db.Column(db.String(20), nullable=False)  # bet_created, stake_placed, resolution, etc.
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
    total_bets = db.Column(db.Integer, default=0)
    total_stakes = db.Column(db.Integer, default=0)
    total_volume_eth = db.Column(db.Numeric(20, 8), default=0)
    total_volume_btc = db.Column(db.Numeric(20, 8), default=0)
    platform_fees_eth = db.Column(db.Numeric(20, 8), default=0)
    platform_fees_btc = db.Column(db.Numeric(20, 8), default=0)
    consensus_accuracy = db.Column(db.Float, default=0.0)
