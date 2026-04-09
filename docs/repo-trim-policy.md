# Repository Trim Policy Rubric

Purpose: governance rubric for deciding whether repo surface area should stay,
hide, deprecate, or be removed.
Authority: reference.
Read when: evaluating commands, scripts, helpers, or docs for scope changes.

This rubric is the decision authority for repository scope changes.

## Evaluation Criteria

Score each criterion explicitly before deciding an outcome.

### 1. Frequency Of Use

Classify based on current operator behavior:

- **Weekly**: used in routine workflows, incident response, or frequent
  platform maintenance.
- **Monthly**: used for recurring but non-routine work such as upgrades,
  audits, or lifecycle operations.
- **Rare**: used only for one-off migrations, historical context, or
  exceptional situations.

### 2. Blast Radius If Removed

Estimate the impact if the item no longer exists:

- **High**: removal can break bootstrap, safety checks, security posture,
  production changes, or recovery paths.
- **Medium**: removal creates friction or manual work, but core operations
  remain possible.
- **Low**: removal has little operational impact and easy alternatives exist.

### 3. Maintenance Cost

Estimate ongoing cost to keep the item accurate and usable:

- **High**: frequent updates, deep context, fragile integrations, or repeated
  troubleshooting
- **Medium**: occasional updates as adjacent systems evolve
- **Low**: stable, rarely changes, and easy to validate

### 4. Runtime Or Cognitive Cost

Evaluate both execution overhead and human complexity:

- **High**: slow, expensive, noisy, or difficult to understand and use
- **Medium**: moderate time or complexity overhead with clear instructions
- **Low**: fast, simple, and low mental load

### 5. Unique Value Vs Duplication

Determine whether the item is canonical or redundant:

- **Unique/Canonical**: provides irreplaceable behavior or authoritative
  documentation
- **Partial overlap**: some duplicated behavior or content; can be
  consolidated
- **Duplicate**: substantially replaced by another maintained command, doc, or
  script

## Outcomes

Assign exactly one outcome to each item.

### `keep`

Use when the item has meaningful current value and should remain visible.

Typical signals:

- frequency is weekly or monthly
- blast radius is high or medium
- unique value is canonical or difficult to replace
- maintenance and runtime or cognitive cost are justified

### `keep-but-hide`

Use when the item is still needed but should not be a default path.

Typical signals:

- frequency is rare
- blast radius is medium or high for edge cases
- the item has niche but legitimate value
- high cognitive or runtime cost suggests restricting discoverability

Action: remove it from primary quickstart docs and default help paths while
keeping it documented in advanced or break-glass material.

### `deprecate`

Use when value is declining and a replacement or consolidation path exists.

Typical signals:

- partial overlap or duplication with a better-maintained alternative
- maintenance cost is high relative to value
- blast radius is low or medium with a clear migration path

Action: mark it as deprecated, point to the replacement, include a target
removal window, and track remaining dependents.

### `remove`

Use when the item no longer provides justified value.

Typical signals:

- frequency is rare
- blast radius is low
- maintenance or cognitive cost is not justified
- functionality or content is duplicated or obsolete

Action: delete the item and references, note the removal in the PR, and confirm
that no automation or runbook still depends on it.

## Decision Record Template

- **Item**:
- **Frequency** (weekly/monthly/rare):
- **Blast radius** (high/medium/low):
- **Maintenance cost** (high/medium/low):
- **Runtime/cognitive cost** (high/medium/low):
- **Unique value vs duplication** (canonical/overlap/duplicate):
- **Outcome** (`keep` | `keep-but-hide` | `deprecate` | `remove`):
- **Notes / migration plan**:
