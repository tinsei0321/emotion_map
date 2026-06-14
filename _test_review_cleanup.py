"""Review fix verification — tests that deleted functions/consts are gone."""
import sys
sys.path.insert(0, '.')

results = []

# Test 1: deleted functions should raise ImportError
for name in ['step2_filter_by_boundary', 'anonymize_dataframe', 'step3_export_filtered']:
    try:
        exec(f'from SCRIPT.data_governance import {name}')
        results.append(f'[❌] {name} still importable')
    except ImportError:
        results.append(f'[OK] {name} correctly removed')

# Test 2: BUFFER_DISTANCE_M should be gone
try:
    from SCRIPT.data_governance import BUFFER_DISTANCE_M
    results.append('[❌] BUFFER_DISTANCE_M still present')
except ImportError:
    results.append('[OK] BUFFER_DISTANCE_M correctly removed')

# Test 3: valid imports still work
try:
    from SCRIPT.data_governance import step1_load_and_transform, step4_run_l2_analysis
    results.append('[OK] step1_load_and_transform, step4_run_l2_analysis importable')
    from SCRIPT.data_governance import L1_COLUMNS
    has_poi = 'poi' in L1_COLUMNS
    results.append(f'[{"OK" if has_poi else "❌"}] poi in L1_COLUMNS: {has_poi}')
except Exception as e:
    results.append(f'[❌] valid import failed: {e}')

# Test 4: l2_confidence column (not 'confidence') in run_pipeline output
try:
    from SCRIPT.emotion_analysis_v1 import L2_COLUMNS
    results.append(f'[OK] L2_COLUMNS = {L2_COLUMNS}')
except Exception as e:
    results.append(f'[❌] L2_COLUMNS import: {e}')

# Test 5: verify 'confidence' column NOT written in run_pipeline
import ast
with open('SCRIPT/emotion_analysis_v1.py', 'r', encoding='utf-8') as f:
    content = f.read()
has_old = "df['confidence']" in content
has_new = "df['l2_confidence']" in content
results.append(f'[{"❌" if has_old else "OK"}] old confidence column: {has_old}')
results.append(f'[{"OK" if has_new else "❌"}] l2_confidence column: {has_new}')

# Test 6: unused imports gone
imports_ok = all(x not in content for x in ['import geopandas', 'from shapely', 'from pyproj import Transformer, CRS'])
results.append(f'[{"OK" if imports_ok else "❌"}] unused imports cleaned')

print('\n'.join(results))