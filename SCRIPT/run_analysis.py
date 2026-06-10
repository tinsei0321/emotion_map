"""
情绪分析引擎 — 命令行入口
══════════════════════════════════════════════════════════════
用法:
    python SCRIPT/run_analysis.py                     # 默认 SnowNLP
    python SCRIPT/run_analysis.py --engine snownlp    # 显式指定

未来接入 LLM 后:
    python SCRIPT/run_analysis.py --engine llm --api-key xxx
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emotion_analysis_v1 import create_analyzer, run_pipeline, export_results

# ── 选择引擎 ──
engine = create_analyzer('snownlp')  # 改 'llm' 即可切换

print(f'引擎: {engine.name} v{engine.version}')
print(f'能力: {engine.get_capabilities()}\n')

# ── 运行管道 ──
df = run_pipeline('data/raw/test_0609_1.csv', engine)

# ── 导出 ──
if not df.empty:
    export_results(df, 'test_0609_v1')
    print('\n完成！')
