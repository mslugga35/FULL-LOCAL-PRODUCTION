# Formatter Test Analysis

## ✅ What's Working Well

1. **Capper Detection**: Successfully identifying and canonicalizing capper names
   - `DuckInvestments` → **DuckInvestments**
   - `nickycashin` → **Nicky Cashin**
   - `cblez.` → **Cblez**
   - `vegasmira` → **vegasmirabet**

2. **No-Play Detection**: Correctly detecting and summarizing no-play messages
   - "No bet tonight - off day" → "No official play today — back tomorrow."

3. **Noise Filtering**: Removing "CAPPERS FREE", "@cappersfree", etc.

## ❌ Issues Found

### 1. Pick Parsing Problems
The `_split_lines()` and `_format_pick()` functions are breaking up picks incorrectly:

**Input**: `MLB: Brewers -1.5 (+110) 2u`
**Current Output**: `@DuckInvestments MLB: Brewers 1.5 () NBA: Warriors ML +110 (2 Unit)`

**Issues**:
- Odds format `(+110)` being split incorrectly
- Multiple picks getting merged into one line
- Line splitting is too aggressive

### 2. Line Splitting Too Aggressive
The regex `r'(?:\s*[•·\-–—]\s*|\s{2,}|,|\||;|\n)'` is splitting on too many characters, breaking up legitimate pick content.

### 3. Unit Format Recognition
- `(1U)` being converted to `() (1 Unit)` - parentheses handling issue
- `2u` working correctly → `(2 Unit)`

## 🔧 Recommended Fixes

### 1. Improve Line Splitting
```python
def _split_lines(cleaned: str):
    # Split more conservatively - primarily on newlines and clear separators
    parts = re.split(r'(?:\n|(?:\s*[•·]\s*)|(?:\s{3,}))', cleaned)
    return [s.strip() for s in parts if s and len(s.strip()) >= 3]
```

### 2. Fix Pick Recognition
The `_looks_like_pick()` function is working, but `_format_pick()` needs to preserve the original structure better:

```python
def _format_pick(s: str) -> str:
    # Extract components more carefully
    odds_match = re.search(r'\(([+-]\d{2,4})\)', s)  # Look for odds in parentheses
    units_match = re.search(r'(\d+\.?\d*)\s*u\b', s, re.I)
    
    # Remove extracted parts while preserving structure
    clean = s
    if odds_match:
        clean = clean.replace(odds_match.group(0), '').strip()
    if units_match:
        clean = re.sub(r'\d+\.?\d*\s*u\b', '', clean, flags=re.I).strip()
    
    # Rebuild with proper formatting
    parts = [clean]
    if odds_match:
        parts.append(odds_match.group(1))
    if units_match:
        parts.append(f"{units_match.group(1)}u")
    
    return ' '.join(parts)
```

### 3. Better Content Preservation
The current approach is too aggressive in breaking up text. Consider preserving more of the original structure and only removing clear noise patterns.

## 📊 Test Results Summary

| Test Case | Capper ID | Pick Extraction | Overall |
|-----------|-----------|-----------------|---------|
| DuckInvestments | ✅ | ❌ | 🟡 |
| Travy | ✅ | ❌ | 🟡 |
| YourDailyCapper | ✅ | ❌ | 🟡 |
| CBLEZ | ✅ | ❌ | 🟡 |
| No-play | ✅ | ✅ | ✅ |
| Alias Test | ✅ | ❌ | 🟡 |
| Promo Spam | ❌ | N/A | ❌ |

**Success Rate**: 
- Capper Detection: 86% (6/7)
- Pick Formatting: 14% (1/7) 
- Overall: 43% (3/7)

## 🎯 Next Steps

1. **Fix line splitting** to be less aggressive
2. **Improve pick formatting** to preserve structure
3. **Test with more realistic content** from actual images
4. **Add better fallback** for unrecognized content

The core framework is solid, but the text processing needs refinement for better pick extraction.