"""
情绪分析引擎 — 命令行入口 v1.0（L2/L3/L4 三级架构）
══════════════════════════════════════════════════════════════
用法:
    # 命令行模式
    python SCRIPT/run_analysis.py
    python SCRIPT/run_analysis.py --file data/raw/xxx.csv --engine snownlp
    python SCRIPT/run_analysis.py --engine llm --api-key sk-xxx

    # GUI 模式（无参数启动默认进入 GUI）
    python SCRIPT/run_analysis.py --gui
"""
import sys, os, json, argparse, threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 修复 Windows GBK 控制台 emoji 编码问题
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from emotion_analysis_v1 import run_analysis_task


# ═══════════════════════════════════════════════════════════
# GUI 模式（Tkinter）
# ═══════════════════════════════════════════════════════════

def launch_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title('情绪地图 v1.0 — 城市情绪数据分析引擎')
    root.geometry('540x520')
    root.resizable(False, False)
    root.configure(bg='#f0f2f5')

    # ── ttk 主题 ──
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Card.TLabelframe', background='white', borderwidth=1, relief='solid')
    style.configure('Card.TLabelframe.Label', background='white', font=('', 10, 'bold'))
    style.configure('Run.TButton', font=('', 12, 'bold'), padding=10)
    style.configure('Browse.TButton', padding=4)

    # ── 标题 ──
    title_frm = tk.Frame(root, bg='#1a73e8', height=52)
    title_frm.pack(fill='x')
    title_frm.pack_propagate(False)
    tk.Label(title_frm, text='🔬  城市情绪数据分析引擎', fg='white', bg='#1a73e8',
             font=('Microsoft YaHei UI', 14, 'bold')).pack(side='left', padx=20, pady=10)
    tk.Label(title_frm, text='v1.0  L2/L3/L4', fg='#b3d4ff', bg='#1a73e8',
             font=('', 9)).pack(side='right', padx=20, pady=10)

    # ── 主内容区 ──
    main_frm = tk.Frame(root, bg='#f0f2f5')
    main_frm.pack(fill='both', expand=True, padx=12, pady=12)

    # ── 卡片：文件选择 ──
    file_card = ttk.Labelframe(main_frm, text='  [DATA]  原始情绪DATA文件（L1）', style='Card.TLabelframe')
    file_card.pack(fill='x', pady=(0, 8))

    file_inner = tk.Frame(file_card, bg='white')
    file_inner.pack(fill='x', padx=12, pady=10)
    file_var = tk.StringVar()
    tk.Entry(file_inner, textvariable=file_var, font=('', 10), relief='solid',
             bd=1).pack(side='left', fill='x', expand=True, ipady=3)
    ttk.Button(file_inner, text='📁 浏览', style='Browse.TButton',
               command=lambda: file_var.set(
                   filedialog.askopenfilename(
                       initialdir='data/raw',
                       filetypes=[('数据文件', '*.csv *.tsv *.json *.geojson'), ('全部', '*.*')]
                   ) or file_var.get()
               )).pack(side='right', padx=(8, 0))

    # ── 卡片：引擎选择 ──
    eng_card = ttk.Labelframe(main_frm, text='  🧠  分析引擎', style='Card.TLabelframe')
    eng_card.pack(fill='x', pady=(0, 8))

    eng_inner = tk.Frame(eng_card, bg='white')
    eng_inner.pack(fill='x', padx=12, pady=8)
    engine_var = tk.StringVar(value='snownlp')

    engines = [
        ('L2 · SnowNLP（离线 / 粗粒度 / 情绪极性）', 'snownlp'),
        ('L3 · LLM 语义增强（需 API Key）', 'llm'),
        ('L4 · 多维归因（需语料库 + API Key）', 'corpus'),
        ('🚀 全管道 L2 → L3 → L4', 'full'),
    ]
    for text, val in engines:
        tk.Radiobutton(eng_inner, text=text, variable=engine_var, value=val,
                       font=('', 10), bg='white', anchor='w',
                       activebackground='#e8f0fe', selectcolor='white',
                       padx=8, pady=2).pack(fill='x')

    # ── 卡片：参数配置 ──
    param_card = ttk.Labelframe(main_frm, text='  ⚙  参数配置', style='Card.TLabelframe')
    param_card.pack(fill='x', pady=(0, 8))

    param_inner = tk.Frame(param_card, bg='white')
    param_inner.pack(fill='x', padx=12, pady=8)

    # API Key
    tk.Label(param_inner, text='🔑 API Key', font=('', 9), bg='white',
             fg='#555').pack(anchor='w')
    api_var = tk.StringVar()
    tk.Entry(param_inner, textvariable=api_var, font=('', 10), show='•', relief='solid',
             bd=1).pack(fill='x', ipady=3, pady=(2, 8))

    # 输出文件名
    tk.Label(param_inner, text='📁 输出文件名', font=('', 9), bg='white',
             fg='#555').pack(anchor='w')
    out_var = tk.StringVar(value='analysis_output')
    tk.Entry(param_inner, textvariable=out_var, font=('', 10), relief='solid',
             bd=1).pack(fill='x', ipady=3, pady=(2, 0))

    # ── 状态栏 ──
    status_frm = tk.Frame(main_frm, bg='#e8eaed', height=36)
    status_frm.pack(fill='x', pady=(0, 8))
    status_frm.pack_propagate(False)
    status_var = tk.StringVar(value='✅ 就绪 — 请选择数据文件并点击开始分析')
    status_label = tk.Label(status_frm, textvariable=status_var, bg='#e8eaed',
                            fg='#444', font=('', 9), anchor='w')
    status_label.pack(side='left', fill='x', padx=12, pady=8)

    # ── 进度条 ──
    progress = ttk.Progressbar(main_frm, mode='indeterminate')
    progress.pack(fill='x')

    # ── 运行按钮 ──
    def _run():
        file_path = file_var.get().strip()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror('错误', '请选择有效的原始数据文件')
            return

        engine = engine_var.get()
        api_key = api_var.get().strip()
        output_name = out_var.get().strip() or 'analysis_output'

        run_btn.config(state='disabled')
        progress.start()
        status_var.set('⏳ 正在分析中，请稍候…')
        status_label.config(fg='#1a73e8')

        def _worker():
            result = run_analysis_task(
                file_path=file_path,
                engine_type=engine if engine != 'full' else 'snownlp',
                output_name=output_name,
                api_key=api_key,
                full_pipeline=(engine == 'full'),
                l3_api_key=api_key,
                l4_api_key=api_key,
            )

            if result['success']:
                root.after(0, lambda: [
                    status_var.set(result['message']),
                    status_label.config(fg='#1a7a1a'),
                    progress.stop(),
                    run_btn.config(state='normal'),
                    messagebox.showinfo('分析完成',
                        f"{result['message']}\n"
                        f"输出: {result['csv_path']}")
                ])
            else:
                root.after(0, lambda: [
                    status_var.set(result['message']),
                    status_label.config(fg='#dc3545'),
                    progress.stop(),
                    run_btn.config(state='normal'),
                ])

        threading.Thread(target=_worker, daemon=True).start()

    btn_frm = tk.Frame(main_frm, bg='#f0f2f5')
    btn_frm.pack(fill='x', pady=(8, 0))
    run_btn = tk.Button(btn_frm, text='🚀  开始分析', command=_run,
                        bg='#1a73e8', fg='white', font=('Microsoft YaHei UI', 12, 'bold'),
                        activebackground='#1557b0', activeforeground='white',
                        relief='flat', cursor='hand2', height=2)
    run_btn.pack(fill='x', ipady=4)

    root.mainloop()


# ═══════════════════════════════════════════════════════════
# 命令行模式
# ═══════════════════════════════════════════════════════════

def main_cli():
    parser = argparse.ArgumentParser(
        description='情绪地图 v1.0 — L2/L3/L4 情绪分析引擎',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python SCRIPT/run_analysis.py                             # 启动 GUI
  python SCRIPT/run_analysis.py --cli                       # 命令行默认参数
  python SCRIPT/run_analysis.py --cli --file data/raw/my_data.csv
  python SCRIPT/run_analysis.py --cli --engine llm --api-key sk-xxx
        """,
    )
    parser.add_argument('--gui', action='store_true', default=True,
                        help='启动 GUI 界面（默认）')
    parser.add_argument('--cli', action='store_true',
                        help='命令行模式')
    parser.add_argument('--engine', default='snownlp',
                        choices=['snownlp', 'llm', 'corpus'],
                        help='分析引擎')
    parser.add_argument('--file', default='data/raw/test_0609_1.csv',
                        help='输入文件路径')
    parser.add_argument('--output', default='emotion_analysis_output',
                        help='输出文件基础名')
    parser.add_argument('--api-key', default='',
                        help='LLM API Key')
    parser.add_argument('--corpus', default='',
                        help='L4 语料库路径')
    parser.add_argument('--full', action='store_true',
                        help='全管道 L2→L3→L4')
    parser.add_argument('--l3-key', default='',
                        help='全管道 L3 API Key')
    parser.add_argument('--l4-key', default='',
                        help='全管道 L4 API Key')
    args = parser.parse_args()

    # 无 --cli 且无特殊参数时，启动 GUI
    if not args.cli and not any([
        args.full, args.api_key, args.l3_key, args.l4_key,
        args.engine != 'snownlp',
    ]):
        launch_gui()
        return

    result = run_analysis_task(
        file_path=args.file,
        engine_type=args.engine,
        output_name=args.output,
        api_key=args.api_key,
        corpus_path=args.corpus,
        full_pipeline=args.full,
        l3_api_key=args.l3_key,
        l4_api_key=args.l4_key,
    )

    if result['success']:
        print(f"\n[OK] {result['message']}")
        print(f"   输出: {result['csv_path']}")
        if result['geojson_path']:
            print(f"         {result['geojson_path']}")
        stats = result['polarity_stats']
        print(f"   分布: V.Neg={stats['Very Negative']} "
              f"Neg={stats['Negative']} "
              f"Neu={stats['Neutral']} "
              f"Pos={stats['Positive']} "
              f"V.Pos={stats['Very Positive']}")
    else:
        print(f"\n[ERR] {result['message']}")


if __name__ == '__main__':
    main_cli()
