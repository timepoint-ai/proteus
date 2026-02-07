#!/usr/bin/env python3
"""
Seed the 6 worked-example markets on BASE Sepolia.

Two-phase workflow:
  1. python scripts/seed_examples.py              # create markets + submissions
  2. python scripts/seed_examples.py --resolve     # resolve markets after they end

Flags:
  --dry-run   Print transactions without sending
  --resolve   Resolve previously created markets (reads state from .seed_state.json)

Env vars:
  OWNER_PRIVATE_KEY      Contract owner (createMarket + resolveMarket)
  TEST_WALLET_KEY_1      Submitter wallet 1
  TEST_WALLET_KEY_2      Submitter wallet 2
  TEST_WALLET_KEY_3      Submitter wallet 3
  TEST_WALLET_KEY_4      Submitter wallet 4
  BASE_SEPOLIA_RPC_URL   RPC endpoint (default: https://sepolia.base.org)

Null prediction handling:
  The contract reverts on empty strings (EmptyPrediction() error). For markets
  where the actual text is "nothing posted," use the __NULL__ sentinel for both
  submission and resolution. distance("__NULL__", "__NULL__") = 0.
"""

import argparse
import json
import os
import sys
import time
import logging

from web3 import Web3
from eth_account import Account

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTRACT_ADDRESS = "0x5174Da96BCA87c78591038DEe9DB1811288c9286"
ABI_PATH = "artifacts/contracts/src/PredictionMarketV2.sol/PredictionMarketV2.json"
STATE_FILE = "scripts/.seed_state.json"
CHAIN_ID = 84532  # BASE Sepolia
MARKET_DURATION = 3600  # 1 hour
MIN_BET_WEI = Web3.to_wei(0.001, "ether")

# ---------------------------------------------------------------------------
# The 6 worked examples
# ---------------------------------------------------------------------------

EXAMPLES = [
    {
        "name": "Example 1: AI Roleplay Wins",
        "actor": "elonmusk",
        "actual": "Starship flight 2 is GO for March. Humanity becomes multiplanetary or we die trying.",
        "submissions": [
            # (wallet_key_env, predicted_text, expected_distance)
            ("TEST_WALLET_KEY_1", "Starship flight 2 confirmed for March. Humanity becomes multiplanetary or dies trying.", 12),
            ("TEST_WALLET_KEY_2", "Elon will probably tweet about SpaceX rockets going to space soon", 66),
            ("TEST_WALLET_KEY_3", "The future of humanity is Mars and beyond", 59),
            ("TEST_WALLET_KEY_4", "a8j3kd9xmz pqlw7 MARS ufk2 rocket lol", 72),
        ],
    },
    {
        "name": "Example 2: Human Insider Beats AI",
        "actor": "sama",
        "actual": "we are now confident AGI is achievable with current techniques. announcement soon.",
        "submissions": [
            ("TEST_WALLET_KEY_1", "we are now confident AGI is achievable with current techniques. big announcement soon.", 4),
            ("TEST_WALLET_KEY_2", "we now believe AGI is achievable with current techniques. announcement coming soon.", 18),
            ("TEST_WALLET_KEY_3", "Sam will say AGI is close again like he always does nothing new", 59),
        ],
    },
    {
        "name": "Example 3: Insider Leaks Exact Wording",
        "actor": "zuck",
        "actual": "Introducing Meta Ray-Ban with live AI translation. 12 languages. The future is on your face.",
        "submissions": [
            ("TEST_WALLET_KEY_1", "Introducing Meta Ray-Ban with live AI translation in 12 languages. The future is on your face.", 3),
            ("TEST_WALLET_KEY_2", "Introducing Meta Ray-Ban AI glasses with real-time translation in 8 languages. The future is on your face.", 25),
            ("TEST_WALLET_KEY_3", "zuck will announce glasses or something idk", 73),
            ("TEST_WALLET_KEY_4", "BUY META NOW GLASSES MOONSHOT 1000X GUARANTEED", 83),
        ],
    },
    {
        "name": "Example 4: Null Submission Wins",
        "actor": "JensenHuang",
        # __NULL__ sentinel: the person didn't post anything
        "actual": "__NULL__",
        "submissions": [
            ("TEST_WALLET_KEY_1", "__NULL__", 0),
            ("TEST_WALLET_KEY_2", "Jensen will flex about Blackwell sales numbers", 46),
            ("TEST_WALLET_KEY_3", "NVIDIA Blackwell Ultra is sampling ahead of schedule. The next era of computing starts now.", 90),
        ],
    },
    {
        "name": "Example 5: AI vs AI Race (Thesis Example)",
        "actor": "sataborasu",
        "actual": "Copilot is now generating 46% of all new code at GitHub-connected enterprises. The AI transformation of software is just beginning.",
        "submissions": [
            ("TEST_WALLET_KEY_1", "Copilot is now generating 45% of all new code at GitHub-connected enterprises. The AI transformation of software is just beginning.", 1),
            ("TEST_WALLET_KEY_2", "Copilot is now generating 43% of all new code at GitHub-connected enterprises. The AI transformation of software has just begun.", 8),
            ("TEST_WALLET_KEY_3", "Microsoft AI is great and will change the world of coding forever", 101),
        ],
    },
    {
        "name": "Example 6: Bot Entropy Wastes Money",
        "actor": "tim_cook",
        "actual": "Apple Intelligence is now available in 30 countries. Privacy and AI, together.",
        "submissions": [
            ("TEST_WALLET_KEY_1", "Apple Intelligence is now available in 24 countries. We believe privacy and AI go hand in hand.", 28),
            ("TEST_WALLET_KEY_2", "Tim will say something about privacy and AI like always", 53),
            ("TEST_WALLET_KEY_3", "x7g APPLE j2m PHONE kq9 BUY zw3 intelligence p5 cook", 65),
            ("TEST_WALLET_KEY_4", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 73),
        ],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_abi():
    with open(ABI_PATH, "r") as f:
        return json.load(f)["abi"]


def get_w3():
    rpc = os.environ.get("BASE_SEPOLIA_RPC_URL", "https://sepolia.base.org")
    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        logger.error("Cannot connect to %s", rpc)
        sys.exit(1)
    return w3


def send_tx(w3, tx, private_key):
    """Sign, send, and wait for a transaction. Returns receipt."""
    account = Account.from_key(private_key)
    tx["from"] = account.address
    tx["nonce"] = w3.eth.get_transaction_count(account.address)
    tx["chainId"] = CHAIN_ID
    if "gas" not in tx:
        tx["gas"] = w3.eth.estimate_gas(tx)
    tx["maxFeePerGas"] = w3.eth.gas_price * 2
    tx["maxPriorityFeePerGas"] = w3.to_wei(0.1, "gwei")

    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    logger.info("  tx sent: %s", tx_hash.hex())
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt["status"] != 1:
        logger.error("  tx REVERTED: %s", tx_hash.hex())
        sys.exit(1)
    return receipt


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    logger.info("State saved to %s", STATE_FILE)


def load_state():
    if not os.path.exists(STATE_FILE):
        logger.error("No state file found at %s -- run without --resolve first", STATE_FILE)
        sys.exit(1)
    with open(STATE_FILE, "r") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Phase 1: Create markets + submissions
# ---------------------------------------------------------------------------

def create_markets(dry_run=False):
    owner_key = os.environ.get("OWNER_PRIVATE_KEY")
    if not owner_key and not dry_run:
        logger.error("OWNER_PRIVATE_KEY is required (or use --dry-run)")
        sys.exit(1)

    if dry_run:
        logger.info("[DRY RUN] No transactions will be sent.\n")
        for ex in EXAMPLES:
            logger.info("=== %s (actor: @%s) ===", ex["name"], ex["actor"])
            logger.info("  createMarket('%s', %d)", ex["actor"], MARKET_DURATION)
            for wallet_env, text, expected_dist in ex["submissions"]:
                logger.info("  createSubmission(marketId, '%s')  [expected dist=%d, wallet=%s]",
                            text[:60] + ("..." if len(text) > 60 else ""),
                            expected_dist, wallet_env)
            logger.info("  resolveMarket(marketId, '%s')",
                        ex["actual"][:60] + ("..." if len(ex["actual"]) > 60 else ""))
            logger.info("")

        logger.info("[DRY RUN] Would create %d markets with %d total submissions",
                    len(EXAMPLES),
                    sum(len(e["submissions"]) for e in EXAMPLES))
        return

    w3 = get_w3()
    abi = load_abi()
    contract = w3.eth.contract(
        address=w3.to_checksum_address(CONTRACT_ADDRESS), abi=abi
    )

    state = {"markets": []}

    for ex in EXAMPLES:
        logger.info("=== %s (actor: @%s) ===", ex["name"], ex["actor"])

        # --- createMarket (owner only) ---
        tx = contract.functions.createMarket(
            ex["actor"], MARKET_DURATION
        ).build_transaction({"value": 0})
        receipt = send_tx(w3, tx, owner_key)

        market_id = None
        if receipt:
            # Parse MarketCreated event to get marketId
            logs = contract.events.MarketCreated().process_receipt(receipt)
            if logs:
                market_id = logs[0]["args"]["marketId"]
            else:
                # Fallback: read marketCount
                market_id = contract.functions.marketCount().call() - 1
            logger.info("  Market created: id=%s", market_id)

        market_state = {
            "name": ex["name"],
            "actor": ex["actor"],
            "market_id": market_id,
            "actual": ex["actual"],
            "submissions": [],
        }

        # --- createSubmission for each submitter ---
        for wallet_env, text, expected_dist in ex["submissions"]:
            wallet_key = os.environ.get(wallet_env)
            if not wallet_key:
                logger.warning("  Skipping submission: %s not set", wallet_env)
                continue

            logger.info("  Submitting (%s): %.60s... [expected dist=%d]",
                        wallet_env, text, expected_dist)

            tx = contract.functions.createSubmission(
                market_id, text
            ).build_transaction({"value": MIN_BET_WEI})
            receipt = send_tx(w3, tx, wallet_key)

            sub_id = None
            if receipt:
                logs = contract.events.SubmissionCreated().process_receipt(receipt)
                if logs:
                    sub_id = logs[0]["args"]["submissionId"]
                else:
                    sub_id = contract.functions.submissionCount().call() - 1
                logger.info("  Submission created: id=%s", sub_id)

            market_state["submissions"].append({
                "wallet_env": wallet_env,
                "text": text,
                "expected_distance": expected_dist,
                "submission_id": sub_id,
            })

        state["markets"].append(market_state)

    save_state(state)
    logger.info("Phase 1 complete. Wait for markets to end, then run with --resolve.")


# ---------------------------------------------------------------------------
# Phase 2: Resolve markets
# ---------------------------------------------------------------------------

def resolve_markets(dry_run=False):
    owner_key = os.environ.get("OWNER_PRIVATE_KEY")
    if not owner_key and not dry_run:
        logger.error("OWNER_PRIVATE_KEY is required (or use --dry-run)")
        sys.exit(1)

    if dry_run:
        logger.info("[DRY RUN] No transactions will be sent.\n")
        for ex in EXAMPLES:
            logger.info("=== Resolving %s (actor: @%s) ===", ex["name"], ex["actor"])
            logger.info("  resolveMarket(marketId, '%s')",
                        ex["actual"][:60] + ("..." if len(ex["actual"]) > 60 else ""))
        logger.info("\n[DRY RUN] Would resolve %d markets", len(EXAMPLES))
        return

    state = load_state()
    w3 = get_w3()
    abi = load_abi()
    contract = w3.eth.contract(
        address=w3.to_checksum_address(CONTRACT_ADDRESS), abi=abi
    )

    for mkt in state["markets"]:
        market_id = mkt["market_id"]
        actual = mkt["actual"]
        logger.info("=== Resolving %s (id=%s) ===", mkt["name"], market_id)

        # Check if market has ended
        details = contract.functions.getMarketDetails(market_id).call()
        end_time = details[2]  # endTime field
        now = w3.eth.get_block("latest")["timestamp"]
        if now < end_time:
            remaining = end_time - now
            logger.warning("  Market %s hasn't ended yet. %ds remaining. Skipping.",
                           market_id, remaining)
            continue

        logger.info("  Resolving with: %.60s...", actual)
        tx = contract.functions.resolveMarket(
            market_id, actual
        ).build_transaction({"value": 0})
        receipt = send_tx(w3, tx, owner_key)

        if receipt:
            logger.info("  Market %s resolved.", market_id)

    logger.info("Phase 2 complete. Markets resolved.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Seed 6 worked-example markets on BASE Sepolia"
    )
    parser.add_argument(
        "--resolve", action="store_true",
        help="Resolve previously created markets (phase 2)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print transactions without sending"
    )
    args = parser.parse_args()

    if args.resolve:
        resolve_markets(dry_run=args.dry_run)
    else:
        create_markets(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
