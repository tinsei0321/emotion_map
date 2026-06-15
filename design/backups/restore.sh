#!/bin/bash
# UI 一键恢复脚本
# 用法: bash design/backups/restore.sh [备份目录名]
# 示例: bash design/backups/restore.sh ui-20260615-1548

BACKUP_DIR="${1:-ui-20260615-1548}"
SRC="design/backups/$BACKUP_DIR"

if [ ! -d "$SRC" ]; then
    echo "[ERR] 备份目录不存在: $SRC"
    echo "可用备份:"
    ls -d design/backups/ui-* 2>/dev/null
    exit 1
fi

echo "从 $SRC 恢复 UI 文件..."
cp "$SRC/ui_components.py" core/
cp "$SRC/app_main.py" apps/
cp "$SRC/tokens.json" design/
cp "$SRC/tokens.py" design/
cp "$SRC/tokens.css" design/
cp "$SRC/generate_css.py" design/
cp "$SRC/brand-visual.md" docs/

echo "[OK] 恢复完成！重启应用即可。"
echo "恢复的文件:"
ls -la "$SRC/"
