"""
One-shot regenerator — reads updated design/tokens.json and regenerates
design/tokens.css + design/tokens.py with all new color values.

Run: python design/_regen.py
"""
import sys
sys.path.insert(0, 'design')
from generate_css import main
main()
