' PT-CB7 T15: EMC 8080 隐藏式启动器（dsh-emc-entry 经 host.openPath 调用）
' 作用：无终端窗口运行 start.bat（WScript.Shell.Run 窗口样式 0 = 隐藏）。
' 进度显化改由 dsh 对话窗口进度卡承担（双端点探测驱动），不再依赖终端输出。
Set ws = CreateObject("WScript.Shell")
ws.Run chr(34) & "D:\Github\emotion_map\start.bat" & chr(34), 0, False
