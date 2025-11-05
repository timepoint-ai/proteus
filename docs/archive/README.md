# Archived Planning Documents

This directory contains historical planning documents that have been superseded by the consolidated **[GAP_CLOSING_PLAN.md](../../GAP_CLOSING_PLAN.md)**.

## Contents

### CRYPTO-USERS-PLAN.md
**Original Purpose:** Detailed plan for Coinbase Embedded Wallet integration and USDC onramp

**Status:** Archived November 2025

**Superseded By:** GAP_CLOSING_PLAN.md Phase 1 (Frontend Wallet Migration) and Phase 5 (Coinbase Onramp Integration)

**Why Archived:** The plan was fragmented across 5 phases and interleaved with implementation details that are now outdated. The new gap closing plan consolidates the actionable items and updates the timeline.

### CLEAN.md
**Original Purpose:** Phase 7 cleanup checklist and database migration status

**Status:** Archived November 2025

**Superseded By:**
- docs/PHASE7_COMPLETE.md (for completed work)
- GAP_CLOSING_PLAN.md Phase 2 (Security Audit & Testing) for remaining cleanup

**Why Archived:** Phase 7 was marked complete, but the document contained outdated checklist items and was confusing about what remained. The new plan clarifies what's actually left to do.

### LAUNCH.md
**Original Purpose:** Comprehensive launch guide for BASE blockchain deployment

**Status:** Archived November 2025

**Superseded By:** GAP_CLOSING_PLAN.md Phase 3 (Mainnet Deployment), Phase 4 (Genesis NFT Distribution), and Phase 6 (First Markets & User Testing)

**Why Archived:** The launch guide was a high-level reference document with many unchecked items. The new plan provides concrete, dated milestones and specific tasks.

## Accessing Archived Documents

These documents remain available for historical reference and context:

```bash
# View archived documents
ls -la docs/archive/

# Read specific archive
cat docs/archive/CRYPTO-USERS-PLAN.md
```

## Migration to New Plan

All actionable items from these documents have been:
1. **Reviewed** for current relevance
2. **Consolidated** into a single timeline
3. **Updated** with realistic dates and dependencies
4. **Assigned** to specific phases in the gap closing plan

No tasks were lost in the consolidation. Items marked as complete were verified, and incomplete items were incorporated into the new plan with updated context.

## When to Use Archived Docs

**Use archived docs for:**
- Historical context on decision-making
- Understanding the evolution of plans
- Detailed implementation notes that didn't fit in the consolidated plan
- Reference for specific technical approaches

**Don't use archived docs for:**
- Current task tracking
- Timeline planning
- Status updates
- New feature implementation

## Active Planning Document

**All current planning should reference:**

### [GAP_CLOSING_PLAN.md](../../GAP_CLOSING_PLAN.md)

This is the single source of truth for:
- Current project status
- Remaining work
- Timeline and milestones
- Success criteria
- Team assignments
- Budget and resources

---

*Archived: November 3, 2025*
*For questions about these archives, see commit history or open an issue.*
