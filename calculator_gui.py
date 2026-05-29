import tkinter as tk
from tkinter import ttk
import math


class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("简易计算器")
        self.root.geometry("380x540")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        # 状态变量
        self.current_input = "0"
        self.previous_input = ""
        self.current_operator = ""
        self.should_reset_input = False
        self.expression = ""

        # 创建UI
        self.create_widgets()
        self.update_display()

        # 键盘绑定
        self.bind_keyboard()

    def create_widgets(self):
        # 主框架
        main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== 显示区域 =====
        display_frame = tk.Frame(
            main_frame, bg="#ffffff", highlightbackground="#d0d0d0",
            highlightthickness=1, relief=tk.FLAT
        )
        display_frame.pack(fill=tk.X, pady=15)

        # 表达式显示（小字）
        self.expression_label = tk.Label(
            display_frame, text="", anchor=tk.E, font=("Segoe UI", 11),
            fg="#888888", bg="#ffffff", padx=15
        )
        self.expression_label.pack(fill=tk.X, pady=(5, 0))

        # 结果/输入显示（大字）
        self.result_label = tk.Label(
            display_frame, text="0", anchor=tk.E, font=("Segoe UI", 32, "bold"),
            fg="#222222", bg="#ffffff", padx=15
        )
        self.result_label.pack(fill=tk.X, pady=(0, 5))

        # ===== 按钮区域 =====
        btn_frame = tk.Frame(main_frame, bg="#f0f0f0")
        btn_frame.pack(fill=tk.BOTH, expand=True)

        # 颜色方案
        colors = {
            "number": {"bg": "#f5f5f5", "fg": "#333333", "active": "#e8e8e8"},
            "operator": {"bg": "#e8e0f0", "fg": "#7c3aed", "active": "#d5c8e8"},
            "function": {"bg": "#f0eef8", "fg": "#555555", "active": "#e0ddf0"},
            "clear": {"bg": "#fce4e4", "fg": "#e53935", "active": "#f5c6c6"},
            "equal": {"bg": "#7c3aed", "fg": "#ffffff", "active": "#6a2be2"},
        }

        # 按钮布局：5行 x 4列
        # (文字, 类型, 列数)
        buttons = [
            # 第1行 - 功能行
            [("C", "clear", 1), ("±", "function", 1), ("←", "function", 1), ("÷", "operator", 1)],
            # 第2行
            [("7", "number", 1), ("8", "number", 1), ("9", "number", 1), ("×", "operator", 1)],
            # 第3行
            [("4", "number", 1), ("5", "number", 1), ("6", "number", 1), ("−", "operator", 1)],
            # 第4行
            [("1", "number", 1), ("2", "number", 1), ("3", "number", 1), ("+", "operator", 1)],
            # 第5行 - 新增指数字符
            [("0", "number", 2), (".", "number", 1), ("xʸ", "operator", 1)],
            # 第6行 - 特殊功能行
            [("%", "function", 1), ("√", "function", 1), ("x²", "function", 1), ("=", "equal", 1)],
        ]

        # 创建按钮
        for row_idx, row in enumerate(buttons):
            row_frame = tk.Frame(btn_frame, bg="#f0f0f0")
            row_frame.pack(fill=tk.X, pady=3)

            for col_idx, (text, btn_type, col_span) in enumerate(row):
                btn = tk.Button(
                    row_frame,
                    text=text,
                    font=("Segoe UI", 15, "bold" if btn_type in ("operator", "equal") else "normal"),
                    bg=colors[btn_type]["bg"],
                    fg=colors[btn_type]["fg"],
                    activebackground=colors[btn_type]["active"],
                    activeforeground=colors[btn_type]["fg"],
                    relief=tk.FLAT,
                    bd=0,
                    padx=8,
                    pady=10,
                    cursor="hand2",
                    command=lambda t=text: self.button_click(t),
                )

                # 按钮悬浮效果
                btn.bind("<Enter>",
                         lambda e, b=btn, ct=colors[btn_type]: b.configure(bg=ct["active"]))
                btn.bind("<Leave>",
                         lambda e, b=btn, ct=colors[btn_type]: b.configure(bg=ct["bg"]))

                btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        # 底部信息
        footer = tk.Label(
            main_frame, text="简易计算器 · 支持键盘操作 · 可用: √ x² xʸ",
            font=("Segoe UI", 9), fg="#aaaaaa", bg="#f0f0f0"
        )
        footer.pack(pady=(8, 0))

    def update_display(self):
        """更新显示"""
        display_text = self.current_input
        try:
            num = float(self.current_input)
            if num.is_integer():
                display_text = str(int(num))
            else:
                display_text = self.current_input
                if len(display_text) > 15:
                    display_text = f"{num:.10g}"
        except ValueError:
            pass

        self.result_label.config(text=display_text)
        self.expression_label.config(text=self.expression)

    def button_click(self, text):
        """按钮点击处理"""
        if text.isdigit():
            self.append_number(int(text))
        elif text == ".":
            self.append_decimal()
        elif text == "±":
            self.toggle_sign()
        elif text == "C":
            self.clear_all()
        elif text == "←":
            self.backspace()
        elif text == "xʸ":
            # 指数运算：用 ^ 作为内部运算符
            self.append_operator("^")
        elif text == "x²":
            # 平方运算：立即计算
            self.square()
        elif text == "√":
            # 平方根运算：立即计算
            self.square_root()
        elif text in ("+", "−", "×", "÷", "%"):
            op_map = {"+": "+", "−": "-", "×": "*", "÷": "/", "%": "%"}
            self.append_operator(op_map[text])
        elif text == "=":
            self.calculate()

    def append_number(self, num):
        """追加数字"""
        if self.should_reset_input:
            self.current_input = ""
            self.should_reset_input = False

        if self.current_input == "0" and num != 0:
            self.current_input = ""

        clean = self.current_input.replace("-", "").replace(".", "")
        if len(clean) >= 15:
            return

        self.current_input += str(num)
        self.update_display()

    def append_decimal(self):
        """追加小数点"""
        if self.should_reset_input:
            self.current_input = "0"
            self.should_reset_input = False

        if "." not in self.current_input:
            self.current_input += "."

        self.update_display()

    def toggle_sign(self):
        """切换正负号"""
        if self.current_input == "0":
            return

        if self.current_input.startswith("-"):
            self.current_input = self.current_input[1:]
        else:
            self.current_input = "-" + self.current_input

        self.update_display()

    def append_operator(self, op):
        """追加二元运算符"""
        if self.current_operator and not self.should_reset_input:
            self.calculate(is_chained=True)

        self.previous_input = self.current_input
        self.current_operator = op
        self.should_reset_input = True

        # 更新表达式显示符号
        op_symbols = {
            "+": "+", "-": "−", "*": "×", "/": "÷",
            "%": "%", "^": "xʸ"
        }
        sym = op_symbols.get(op, op)
        self.expression = f"{self.previous_input} {sym}"

        self.update_display()

    def calculate(self, is_chained=False):
        """执行计算"""
        if not self.current_operator or not self.previous_input:
            return

        try:
            prev = float(self.previous_input)
            curr = float(self.current_input)
            op = self.current_operator

            if op == "+":
                result = prev + curr
            elif op == "-":
                result = prev - curr
            elif op == "*":
                result = prev * curr
            elif op == "/":
                if curr == 0:
                    result = "错误"
                else:
                    result = prev / curr
            elif op == "%":
                result = prev % curr
            elif op == "^":
                # 指数运算: prev 的 curr 次方
                result = prev ** curr
                # 如果结果太大或太小，保持原样
                if abs(result) > 1e100 or (abs(result) < 1e-100 and result != 0):
                    pass
            else:
                return

            # 处理小数精度
            if isinstance(result, float) and not result.is_integer():
                result = round(result, 12)

            # 更新表达式
            op_symbols = {
                "+": "+", "-": "−", "*": "×", "/": "÷",
                "%": "%", "^": "xʸ"
            }
            sym = op_symbols.get(self.current_operator, self.current_operator)
            if not is_chained:
                self.expression = f"{self.previous_input} {sym} {self.current_input} ="

            # 格式化结果
            if isinstance(result, float):
                if result.is_integer():
                    self.current_input = str(int(result))
                else:
                    # 用科学计数法显示极大/极小数字
                    if abs(result) > 1e15 or (abs(result) < 1e-10 and result != 0):
                        self.current_input = f"{result:.10e}"
                    else:
                        self.current_input = str(result)
            else:
                self.current_input = str(result)

            self.previous_input = ""
            self.current_operator = ""
            self.should_reset_input = True

            self.update_display()

        except OverflowError:
            self.current_input = "结果过大"
            self.previous_input = ""
            self.current_operator = ""
            self.should_reset_input = True
            self.update_display()
        except Exception:
            self.current_input = "错误"
            self.previous_input = ""
            self.current_operator = ""
            self.should_reset_input = True
            self.update_display()

    def square(self):
        """计算平方"""
        try:
            num = float(self.current_input)
            result = num ** 2

            self.expression = f"({self.current_input})² ="

            if result.is_integer():
                self.current_input = str(int(result))
            elif abs(result) > 1e15 or (abs(result) < 1e-10 and result != 0):
                self.current_input = f"{result:.10e}"
            else:
                self.current_input = str(round(result, 12))

            self.should_reset_input = True
            self.update_display()
        except Exception:
            self.current_input = "错误"
            self.update_display()

    def square_root(self):
        """计算平方根"""
        try:
            num = float(self.current_input)
            if num < 0:
                self.current_input = "错误"
                self.expression = f"√({self.current_input}) 负数无实数根"
                self.should_reset_input = True
                self.update_display()
                return

            result = math.sqrt(num)

            self.expression = f"√({self.current_input}) ="

            if result.is_integer():
                self.current_input = str(int(result))
            elif abs(result) > 1e15 or (abs(result) < 1e-10 and result != 0):
                self.current_input = f"{result:.10e}"
            else:
                self.current_input = str(round(result, 12))

            self.should_reset_input = True
            self.update_display()
        except Exception:
            self.current_input = "错误"
            self.update_display()

    def clear_all(self):
        """全部清空"""
        self.current_input = "0"
        self.previous_input = ""
        self.current_operator = ""
        self.should_reset_input = False
        self.expression = ""
        self.update_display()

    def backspace(self):
        """退格删除"""
        if self.should_reset_input:
            return

        if len(self.current_input) > 1:
            self.current_input = self.current_input[:-1]
            if self.current_input in ("", "-"):
                self.current_input = "0"
        else:
            self.current_input = "0"

        self.update_display()

    def bind_keyboard(self):
        """绑定键盘事件"""
        self.root.bind("<Key>", self.key_press)

    def key_press(self, event):
        """键盘按键处理"""
        key = event.char

        if key.isdigit():
            self.append_number(int(key))
        elif key == ".":
            self.append_decimal()
        elif key in "+-":
            self.append_operator("+" if key == "+" else "-")
        elif key == "*":
            self.append_operator("*")
        elif key == "/":
            self.append_operator("/")
        elif key == "%":
            self.append_operator("%")
        elif key == "^":
            self.append_operator("^")
        elif key in ("\r", "="):
            self.calculate()
        elif key in ("\x1b", "c", "C"):
            self.clear_all()
        elif key == "\x08":
            self.backspace()


if __name__ == "__main__":
    root = tk.Tk()
    app = Calculator(root)
    root.mainloop()
