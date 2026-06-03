import os
import json

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Emotion Map Viewer")
st.title("Emotion Map Viewer")

BASE_DIRS = {
    "raw_emotion": "data/raw_emotion",
    "emotion_results": "data/emotion_results",
    "scripts": "data/scripts",
}

folder_key = st.sidebar.selectbox("选择数据文件夹", list(BASE_DIRS.keys()))
folder_path = BASE_DIRS[folder_key]

if not os.path.exists(folder_path):
    st.warning(f"文件夹不存在: {folder_path}")
else:
    files = sorted([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
    if not files:
        st.info("所选文件夹中没有文件。")
    else:
        file_choice = st.sidebar.selectbox("选择文件", files)
        file_path = os.path.join(folder_path, file_choice)
        st.write("**文件路径:**", file_path)

        ext = file_choice.lower().split('.')[-1]
        try:
            if ext in ("csv", "tsv"):
                sep = "\t" if ext == "tsv" else ","
                df = pd.read_csv(file_path, sep=sep)
                st.dataframe(df)
                st.download_button("下载为 CSV", df.to_csv(index=False).encode("utf-8"), file_name=file_choice, mime="text/csv")
            elif ext in ("json", "ndjson"):
                if ext == "json":
                    with open(file_path, encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    # ndjson: 每行一个 JSON 对象
                    data = []
                    with open(file_path, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                data.append(json.loads(line))
                st.json(data)
            else:
                with open(file_path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
                st.text_area("文件内容", text, height=400)
        except Exception as e:
            st.error(f"读取文件时出错: {e}")


st.markdown("---")
st.caption("通过侧边栏选择文件夹并打开文件。支持 CSV/TSV/JSON/纯文本。")
