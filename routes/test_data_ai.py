"""Test data generator for AI transparency features"""

import json
import uuid
import random
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Blueprint, jsonify
from models import (
    db, NodeOperator, Actor, PredictionMarket, Submission, Bet, 
    Transaction, AIAgentProfile, BittensorIntegration, 
    VerificationModule, TransparencyAudit
)

test_data_ai_bp = Blueprint('test_data_ai', __name__)

# Sample AI agent data
AI_AGENTS = [
    {
        'id': 'bittensor_subnet_4_uid_123',
        'name': 'GPT-Predictor Alpha',
        'organization': 'DeepMind Labs',
        'subnet_id': 4,
        'neuron_type': 'miner',
        'hotkey': '5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY',
        'transparency_level': 4
    },
    {
        'id': 'bittensor_subnet_7_uid_456',
        'name': 'LLaMA Oracle v2',
        'organization': 'Meta AI Research',
        'subnet_id': 7,
        'neuron_type': 'validator',
        'hotkey': '5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty',
        'transparency_level': 3
    },
    {
        'id': 'custom_agent_789',
        'name': 'Claude Prediction Engine',
        'organization': 'Anthropic',
        'subnet_id': None,
        'neuron_type': None,
        'hotkey': '0x742d35Cc6634C0532925a3b844Bc9e7595f7F123',
        'transparency_level': 2
    },
    {
        'id': 'bittensor_subnet_15_uid_321',
        'name': 'Mistral Forecaster',
        'organization': 'Mistral AI',
        'subnet_id': 15,
        'neuron_type': 'miner',
        'hotkey': '5DAAnrj7VHTznn2AWBemMuyBwZWs6FNFjdyVXUeYum3PTXFy',
        'transparency_level': 4
    }
]

# Sample prediction texts for AI agents
AI_PREDICTIONS = [
    "The Federal Reserve will announce a 25 basis point rate cut in their next FOMC meeting",
    "Tesla's stock price will exceed $300 by the end of Q4 2025",
    "Bitcoin will reach a new all-time high above $100,000 within the next 90 days",
    "OpenAI will release GPT-5 with multimodal capabilities before December 2025",
    "Apple will announce entry into the autonomous vehicle market in 2026",
    "The S&P 500 will experience a correction of at least 10% in the next quarter",
    "Ethereum will successfully implement sharding by Q2 2026",
    "Microsoft will acquire a major gaming studio for over $20 billion",
    "SpaceX will conduct the first crewed mission to Mars before 2030",
    "Quantum computing will achieve commercial viability for cryptography by 2027"
]

# Verification module sample data
MODULE_DATA = {
    'open_source': {
        'ipfs_hash': 'QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco',
        'blockchain_reference': 'ethereum:0x1234567890abcdef1234567890abcdef12345678',
        'model_architecture': {
            'type': 'transformer',
            'layers': 48,
            'hidden_size': 4096,
            'attention_heads': 64,
            'parameters': '175B'
        },
        'training_data_hash': 'sha256:a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'
    },
    'architecture': {
        'architecture_details': {
            'model_type': 'decoder-only transformer',
            'vocab_size': 50257,
            'context_length': 8192,
            'activation': 'gelu',
            'optimizer': 'AdamW',
            'learning_rate': '1e-4',
            'batch_size': 512,
            'training_steps': '1M'
        },
        'training_data_hash': 'sha256:b3d4f67890123abc456def789012efgh345678901234567890abcdef123456'
    },
    'reasoning': {
        'reasoning_trace': {
            'steps': [
                'Analyzed historical Federal Reserve meeting patterns',
                'Evaluated current economic indicators: inflation at 3.2%, unemployment at 3.8%',
                'Compared with similar historical periods (2019, 2007, 1995)',
                'Applied Bayesian inference with prior probability of 0.65',
                'Factored in recent Fed chair statements and dot plot projections',
                'Final confidence: 78% probability of 25bp cut'
            ],
            'confidence_score': 0.78,
            'uncertainty_bounds': [0.72, 0.84]
        },
        'computational_proof': 'zkSNARK:0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
    },
    'audit': {
        'audit_report_hash': 'sha256:ef456789012345678901234567890123456789012345678901234567890123ef',
        'audit_details': {
            'auditor': 'AI Safety Institute',
            'audit_date': '2025-07-15',
            'certification_level': 'Gold',
            'findings': {
                'code_review': 'passed',
                'architecture_validation': 'passed',
                'training_data_verification': 'passed',
                'bias_testing': 'minimal bias detected',
                'robustness_testing': 'passed'
            }
        }
    }
}

@test_data_ai_bp.route('/generate_ai_transparency', methods=['POST'])
def generate_ai_transparency_data():
    """Generate comprehensive test data for AI transparency features"""
    try:
        # Get default node operator
        node = NodeOperator.query.filter_by(status='active').first()
        if not node:
            return jsonify({'error': 'No active node operators found'}), 400
        
        # Get approved actors
        actors = Actor.query.filter_by(status='approved').limit(5).all()
        if not actors:
            return jsonify({'error': 'No approved actors found'}), 400
        
        # Statistics
        stats = {
            'ai_profiles_created': 0,
            'bittensor_integrations': 0,
            'markets_created': 0,
            'ai_submissions': 0,
            'verification_modules': 0,
            'transparency_audits': 0,
            'total_bonuses': Decimal('0')
        }
        
        # Create AI agent profiles
        for agent_data in AI_AGENTS:
            profile = AIAgentProfile.query.filter_by(agent_id=agent_data['id']).first()
            if not profile:
                profile = AIAgentProfile(
                    agent_id=agent_data['id'],
                    agent_name=agent_data['name'],
                    organization=agent_data['organization'],
                    transparency_level=agent_data['transparency_level'],
                    open_source_commitment=(agent_data['transparency_level'] >= 1),
                    architecture_disclosure=(agent_data['transparency_level'] >= 2),
                    reasoning_transparency=(agent_data['transparency_level'] >= 3),
                    audit_participation=(agent_data['transparency_level'] == 4)
                )
                db.session.add(profile)
                stats['ai_profiles_created'] += 1
            
            # Create Bittensor integration if applicable
            if agent_data['subnet_id'] and not BittensorIntegration.query.filter_by(ai_agent_id=agent_data['id']).first():
                integration = BittensorIntegration(
                    ai_agent_id=agent_data['id'],
                    subnet_id=agent_data['subnet_id'],
                    neuron_type=agent_data['neuron_type'],
                    hotkey_address=agent_data['hotkey'],
                    coldkey_address=agent_data['hotkey'][:42],  # Simplified
                    tao_staked=Decimal(str(random.uniform(100, 10000))),
                    yuma_score=random.uniform(0.6, 0.95),
                    trust_score=random.uniform(0.7, 0.98),
                    is_active=True,
                    last_sync=datetime.utcnow()
                )
                db.session.add(integration)
                stats['bittensor_integrations'] += 1
        
        db.session.commit()
        
        # Create markets and AI agent submissions
        for i, actor in enumerate(actors):
            # Create a prediction market
            market = PredictionMarket(
                actor_id=actor.id,
                start_time=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
                end_time=datetime.utcnow() + timedelta(days=random.randint(1, 7)),
                oracle_wallets=json.dumps([f"0x{uuid.uuid4().hex[:40]}" for _ in range(3)]),
                status='active'
            )
            db.session.add(market)
            db.session.flush()
            stats['markets_created'] += 1
            
            # Create AI agent submissions
            for j, agent_data in enumerate(AI_AGENTS[:3]):  # First 3 agents make submissions
                # Determine submission type
                if j == 0:
                    submission_type = 'original'
                else:
                    submission_type = 'competitor'
                
                # Create submission
                submission = Submission(
                    market_id=market.id,
                    creator_wallet=agent_data['hotkey'],
                    predicted_text=random.choice(AI_PREDICTIONS),
                    submission_type=submission_type,
                    initial_stake_amount=Decimal(str(random.uniform(0.5, 5.0))),
                    currency='ETH',
                    transaction_hash=f"0x{uuid.uuid4().hex}{uuid.uuid4().hex}"[:66],
                    is_ai_agent=True,
                    ai_agent_id=agent_data['id'],
                    transparency_level=agent_data['transparency_level']
                )
                db.session.add(submission)
                db.session.flush()
                stats['ai_submissions'] += 1
                
                # Add verification modules based on transparency level
                modules_to_add = []
                if agent_data['transparency_level'] >= 1:
                    modules_to_add.append('open_source')
                if agent_data['transparency_level'] >= 2:
                    modules_to_add.append('architecture')
                if agent_data['transparency_level'] >= 3:
                    modules_to_add.append('reasoning')
                if agent_data['transparency_level'] == 4:
                    modules_to_add.append('audit')
                
                total_bonus = Decimal('0')
                for module_type in modules_to_add:
                    module = VerificationModule(
                        submission_id=submission.id,
                        module_type=module_type,
                        is_verified=True,
                        verification_timestamp=datetime.utcnow(),
                        verification_details=json.dumps({
                            'verified': True,
                            'module_type': module_type,
                            'timestamp': datetime.utcnow().isoformat()
                        })
                    )
                    
                    # Set module-specific data
                    if module_type == 'open_source':
                        module.ipfs_hash = MODULE_DATA['open_source']['ipfs_hash']
                        module.blockchain_reference = MODULE_DATA['open_source']['blockchain_reference']
                        module.model_architecture = json.dumps(MODULE_DATA['open_source']['model_architecture'])
                        module.training_data_hash = MODULE_DATA['open_source']['training_data_hash']
                        module.reward_bonus = Decimal('0.15')
                    elif module_type == 'architecture':
                        module.model_architecture = json.dumps(MODULE_DATA['architecture']['architecture_details'])
                        module.training_data_hash = MODULE_DATA['architecture']['training_data_hash']
                        module.reward_bonus = Decimal('0.20')
                    elif module_type == 'reasoning':
                        module.reasoning_trace = json.dumps(MODULE_DATA['reasoning']['reasoning_trace'])
                        module.computational_proof = MODULE_DATA['reasoning']['computational_proof']
                        module.reward_bonus = Decimal('0.25')
                    elif module_type == 'audit':
                        module.audit_report_hash = MODULE_DATA['audit']['audit_report_hash']
                        module.verification_details = json.dumps(MODULE_DATA['audit']['audit_details'])
                        module.reward_bonus = Decimal('0.35')
                    
                    total_bonus += module.reward_bonus
                    db.session.add(module)
                    stats['verification_modules'] += 1
                
                # Update submission bonus
                submission.total_reward_bonus = min(total_bonus, Decimal('0.95'))
                stats['total_bonuses'] += submission.total_reward_bonus
                
                # Update AI agent profile stats
                profile = AIAgentProfile.query.filter_by(agent_id=agent_data['id']).first()
                if profile:
                    profile.total_submissions += 1
                    profile.total_staked = (profile.total_staked or Decimal('0')) + submission.initial_stake_amount
                
                # Create transparency audit for level 4 agents
                if agent_data['transparency_level'] == 4 and random.random() > 0.5:
                    audit = TransparencyAudit(
                        agent_id=agent_data['id'],
                        auditor_name='AI Safety Institute',
                        auditor_wallet=f"0x{uuid.uuid4().hex[:40]}",
                        audit_type='comprehensive',
                        audit_scope='Full model architecture, training data, and inference process',
                        audit_methodology='ISO 23894 AI Transparency Standard',
                        audit_passed=True,
                        findings=json.dumps({
                            'overall_score': 92,
                            'transparency_rating': 'Excellent',
                            'recommendations': ['Consider open-sourcing evaluation benchmarks']
                        }),
                        audit_hash=MODULE_DATA['audit']['audit_report_hash'],
                        signature=f"0x{uuid.uuid4().hex}{uuid.uuid4().hex}"[:130],
                        expires_at=datetime.utcnow() + timedelta(days=365)
                    )
                    db.session.add(audit)
                    stats['transparency_audits'] += 1
        
        # Create some bets on AI submissions
        ai_submissions = Submission.query.filter_by(is_ai_agent=True).all()
        for submission in ai_submissions[:5]:
            for _ in range(random.randint(2, 5)):
                bet = Bet(
                    submission_id=submission.id,
                    bettor_wallet=f"0x{uuid.uuid4().hex[:40]}",
                    amount=Decimal(str(random.uniform(0.1, 1.0))),
                    currency=submission.currency,
                    transaction_hash=f"0x{uuid.uuid4().hex}{uuid.uuid4().hex}"[:66],
                    status='confirmed'
                )
                db.session.add(bet)
        
        db.session.commit()
        
        return jsonify({
            'message': 'AI transparency test data generated successfully',
            'statistics': {
                'ai_profiles_created': stats['ai_profiles_created'],
                'bittensor_integrations': stats['bittensor_integrations'],
                'markets_created': stats['markets_created'],
                'ai_submissions': stats['ai_submissions'],
                'verification_modules': stats['verification_modules'],
                'transparency_audits': stats['transparency_audits'],
                'total_bonuses_allocated': str(stats['total_bonuses'])
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to generate test data: {str(e)}'}), 500

@test_data_ai_bp.route('/clear_ai_data', methods=['POST'])
def clear_ai_data():
    """Clear all AI transparency related data"""
    try:
        # Delete in order to respect foreign key constraints
        TransparencyAudit.query.delete()
        VerificationModule.query.delete()
        BittensorIntegration.query.delete()
        
        # Clear AI-related submissions and their bets
        ai_submissions = Submission.query.filter_by(is_ai_agent=True).all()
        for submission in ai_submissions:
            Bet.query.filter_by(submission_id=submission.id).delete()
        Submission.query.filter_by(is_ai_agent=True).delete()
        
        AIAgentProfile.query.delete()
        
        db.session.commit()
        
        return jsonify({
            'message': 'AI transparency data cleared successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to clear data: {str(e)}'}), 500