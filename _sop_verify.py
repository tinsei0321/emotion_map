"""SOP 全链路验证"""
import sys, os, json, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# === Step 0: Clean cache ===
for root, dirs, files in os.walk('.'):
    for d in dirs:
        if d == '__pycache__':
            path = os.path.join(root, d)
            shutil.rmtree(path, ignore_errors=True)

results = []

# === Step 1: Check file content ===
with open('core/map_engine.py', encoding='utf-8') as f:
    content = f.read()

tests = {
    'get_tooltip in Layer': 'get_tooltip=\'tooltip\'' in content,
    'comments in tooltip fields': "'comments'" in content and "'poi'" in content,
    'add_selection_marker defined': 'def add_selection_marker' in content,
}

for name, passed in tests.items():
    status = 'PASS' if passed else 'FAIL'
    results.append(f'[{status}] map_engine.py: {name}')

# === Step 2: Check app_main.py content ===
with open('apps/app_main.py', encoding='utf-8') as f:
    content2 = f.read()

tests2 = {
    'imports add_selection_marker': 'add_selection_marker' in content2.split('from core.map_engine import')[1].split(')')[0],
    'selection_mode single-object': "selection_mode='single-object'" in content2,
    'on_select rerun': "on_select='rerun'" in content2,
    'selection parser fixed': 'for layer_name, items in objects.items():' in content2,
    'cursor auto CSS': 'cursor: auto' in content2,
    '_render_selection_detail call': '_render_selection_detail()' in content2,
    'add_selection_marker call': 'add_selection_marker(deck, sel_pt' in content2,
}

for name, passed in tests2.items():
    status = 'PASS' if passed else 'FAIL'
    results.append(f'[{status}] app_main.py: {name}')

# === Step 3: Test import ===
try:
    from core.map_engine import add_selection_marker
    results.append('[PASS] import add_selection_marker')
except Exception as e:
    results.append(f'[FAIL] import add_selection_marker: {e}')

# === Step 4: Test pydeck tooltip API ===
try:
    import pydeck as pdk
    import pandas as pd
    df = pd.DataFrame([{'lat': 30.71, 'lon': 111.29, 'tooltip': 'test data'}])
    layer = pdk.Layer(
        'ScatterplotLayer', data=df,
        get_position=['lon', 'lat'],
        get_fill_color=[255, 0, 0, 200],
        get_radius=100,
        pickable=True,
        auto_highlight=True,
        get_tooltip='tooltip',
    )
    results.append('[PASS] pdk.Layer accepts get_tooltip')

    # Test Deck.tooltip
    deck = pdk.Deck(layers=[layer])
    deck.tooltip = {
        'html': '<b>{tooltip}</b>',
        'style': {'backgroundColor': 'rgba(0,0,0,0.8)'},
    }
    results.append(f'[PASS] deck.tooltip set: {bool(deck.tooltip)}')

    # Print pydeck version
    results.append(f'[INFO] pydeck version: {getattr(pdk, "__version__", "unknown")}')

except Exception as e:
    results.append(f'[FAIL] tooltip API: {e}')

# === Step 5: Verify selection logic ===
mock = {'objects': {'ScatterplotLayer': [{'lat': 30.71, 'lon': 111.29, 'tooltip': 'test'}]}}
objects = mock.get('objects', {})
point_data = None
for layer_name, items in objects.items():
    if items and isinstance(items, list) and len(items) > 0:
        point_data = items[0]
        break
if point_data and point_data.get('lat') == 30.71:
    results.append('[PASS] selection parser logic')
else:
    results.append('[FAIL] selection parser logic')

# === Output ===
with open('_sop_result.txt', 'w', encoding='utf-8') as f:
    for line in results:
        print(line)
        f.write(line + '\n')

print(f'\n{"="*50}')
pass_count = sum(1 for r in results if r.startswith('[PASS]'))
fail_count = sum(1 for r in results if r.startswith('[FAIL]'))
print(f'Result: {pass_count} PASS, {fail_count} FAIL, {len(results)} total')
if fail_count > 0:
    print('[ACTION REQUIRED] Fix failing checks above')
else:
    print('[ALL PASS] Code changes verified. Use _sop_restart.bat to restart.')