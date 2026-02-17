# Proteus - Development Commands

.PHONY: help install test test-unit test-integration test-cov test-contracts test-all lint clean

help:
	@echo "Proteus Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install        Install all dependencies"
	@echo "  install-test   Install test dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run all Python tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-cov       Run tests with coverage report"
	@echo "  test-contracts Run smart contract tests"
	@echo "  test-all       Run all tests (Python + contracts)"
	@echo ""
	@echo "Development:"
	@echo "  run            Start Flask development server"
	@echo "  compile        Compile smart contracts"
	@echo "  deploy-testnet Deploy contracts to BASE Sepolia"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean          Remove build artifacts"

# =============================================================================
# Setup
# =============================================================================

install:
	pip install -e .
	npm install

install-test:
	pip install -e ".[test]"

# =============================================================================
# Testing - Python
# =============================================================================

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

test-cov:
	pytest tests/ --cov=services --cov=routes --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

test-fast:
	pytest tests/unit/ -v -x --tb=short

# =============================================================================
# Testing - Smart Contracts
# =============================================================================

test-contracts:
	npx hardhat test

test-market:
	npx hardhat test contracts/test/PredictionMarket.test.js

test-genesis:
	npx hardhat test contracts/test/GenesisNFT.test.js

test-payout:
	npx hardhat test contracts/test/DistributedPayoutManager.test.js

# =============================================================================
# Testing - All
# =============================================================================

test-all: test-contracts test
	@echo "All tests completed!"

# =============================================================================
# Development
# =============================================================================

run:
	python main.py

compile:
	npx hardhat compile

deploy-testnet:
	npx hardhat run scripts/deploy-genesis-phase1.js --network baseSepolia

# =============================================================================
# Cleanup
# =============================================================================

clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	rm -rf node_modules/.cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
