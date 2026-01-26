# Google Doc Export Improvement Plan

## Current Issues
1. Shows yesterday's results (picks with ✅) mixed with today's picks
2. Shows picks for games not playing today
3. Format has timestamps that show ??:??
4. Hard to copy/paste for consensus

## Requirements (from Matt)
- **Format**: Capper + Pick (e.g., "BeezoWins: Bills -5.5 (2U)")
- **Exclude ✅**: Skip any pick with checkmarks (these are results)
- **Today only**: Cross-reference ESPN to only show today's games

---

## Implementation Plan

### Phase 1: Filter Out Results
Add filtering in `format_content()` to skip picks containing:
- ✅ or ✓ (checkmarks)
- "HIT", "CASH", "WINNER", "W/L" at end of line
- Lines that look like results (e.g., "Eagles ✅ Lions")

**Location**: `src/export_to_gdocs.py` lines 450-520

### Phase 2: ESPN Schedule Validation
Create function to fetch today's games from ESPN API:
- NFL: https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard
- NBA: https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard
- NCAAB: https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard
- NHL: https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard

Extract team names playing today, then filter picks to only include those teams.

**New file**: `src/espn_schedule.py`

### Phase 3: Clean Output Format
Change from:
```
[??:??] **CHAMBA (Max Play)**
```

To:
```
CHAMBA: Bills -5.5 (2U)
```

Group by sport for easy copy:
```
=== NFL ===
BeezoWins: Bills -5.5 (2U)
Caruso: Rams +3 (1U)

=== NBA ===
PropJoe: Lakers -4 (2U)
```

### Phase 4: Deduplication
- Same pick from multiple cappers = show consensus count
- "Bills -5.5 (3 cappers: BeezoWins, Caruso, PropJoe)"

---

## Files to Modify
1. `src/export_to_gdocs.py` - Main export logic
2. `src/espn_schedule.py` - NEW: ESPN API integration
3. `config/settings.yaml` - Add ESPN API config (if needed)

## Estimated Changes
- ~100 lines new ESPN code
- ~50 lines filter logic
- ~30 lines format changes

---

## Quick Win (Can Do Now)
Just add the ✅ filter - this alone removes most result noise:
```python
# Skip result lines
if '✅' in text or '✓' in text:
    continue
```
