import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.map_engine import add_selection_marker
print("add_selection_marker imported OK:", add_selection_marker.__name__)