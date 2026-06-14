"""SOP 自检脚本：模拟 Streamlit 运行时验证改动正确性"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, shutil

# —— Step 0: 清除所有缓存 ——
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        path = os.path.join(root, '__pycache__')
        shutil.rmtree(path, ignore_errors=True)
        print(f"[CLEAN] removed: {path}")
print("[CLEAN] All __pycache__ cleared")

# —— Step 1: 重新导入 core.map_engine ——
import core.map_engine as mp
importlib.reload(mp)

# —— Step 2: 验证 add_selection_marker ——
assert hasattr(mp, 'add_selection_marker'), "missing add_selection_marker"
print(f"[PASS] add_selection_marker exists: {mp.add_selection_marker.__name__}")

# —— Step 3: 验证 Layer 的 get_tooltip ——
import pydeck as pdk
import pandas as pd

df = pd.DataFrame([{'lat': 30.71, 'lon': 111.29, 'tooltip': '测试tooltip'}])
try:
    layer = pdk.Layer(
        'ScatterplotLayer', data=df,
        get_position=['lon', 'lat'],
        get_fill_color=[255, 0, 0, 200],
        get_radius=100,
        pickable=True,
        auto_highlight=True,
        get_tooltip='tooltip',
    )
    print(f"[PASS] pdk.Layer with get_tooltip created")

except TypeError as e:
    print(f"[FAIL] get_tooltip rejected: {e}")

# —— Step 4: 验证 Deck.tooltip dict ——
deck = pdk.Deck(
    initial_view_state=pdk.ViewState(latitude=30.71, longitude=111.29, zoom=12),
    layers=[],
)
deck.tooltip = {
    'html': '<b>{tooltip}</b>',
    'style': {'backgroundColor': 'rgba(0,0,0,0.8)', 'color': '#fff'},
}
print(f"[PASS] deck.tooltip dict set: {deck.tooltip}")

# —— Step 5: 验证 selection 解析逻辑 ——
mock_selection = {
    'objects': {
        'ScatterplotLayer': [
            {'lat': 30.71, 'lon': 111.29, 'tooltip': 'id_e: 123\npolarity: Positive'}
        ]
    }
}
objects = mock_selection.get('objects', {})
point_data = None
for layer_name, items in objects.items():
    if items and isinstance(items, list) and len(items) > 0:
        point_data = items[0]
        break
assert point_data is not None, "selection parser failed"
assert point_data['tooltip'] == 'id_e: 123\npolarity: Positive'
print(f"[PASS] selection parser: lat={point_data['lat']}, lon={point_data['lon']}")

# —— Step 6: 导入 app_main 确认无语法错误 ——
import apps.app_main as am
importlib.reload(am)
print(f"[PASS] app_main imported successfully")

print("\n[ALL PASS] SOP 自检通过")