# ORIGINAL CODE:
from snownlp import SnowNLP
import pandas as pd
import altair as alt
import streamlit as st

comments = [
    "小区绿化率特别高，空气特别清新！",
    "这边太吵了，楼下施工没停过",
    "商圈很方便，餐饮选择多",
    "每次路过都觉得压抑，路灯太暗",
    "公园很美，适合跑步散步"
]

all_comments = []

for i, text in enumerate(comments):
    s = SnowNLP(text).sentiments
    if s > 0.5:
        polarity = "正面"
    elif s < 0.5:
        polarity = "负面"
    else:
        polarity = "中性"
    dict_comments = {
        "id": f"e{i+1:03d}",
        "content": text,
        "score": round(s, 2),
        "polarity": polarity
    }
    all_comments.append(dict_comments)

# Altair 直方图
df_comments = pd.DataFrame(all_comments)
df_count = df_comments['polarity'].value_counts().reset_index()
df_count.columns = ['polarity', 'count']
hist = alt.Chart(df_count).mark_bar().encode(
    x=alt.X('polarity:N', title='情绪极性'),
    y=alt.Y('count:Q', title='评论数量', axis=alt.Axis(format='d')),
    color=alt.Color('polarity:N', legend=None)
).properties(
    title='评论情绪极性分布'
)
# Altair 饼图
pie = alt.Chart(df_count).mark_arc().encode(
    theta=alt.Theta(field="count:Q", type="quantitative"),  # 直接用 count 列，不聚合
    color=alt.Color(field="polarity", type="nominal")
).properties(
    title='评论情绪极性分布'
)

# 在streamlit中显示结果
# 不加端口（默认端口8501）：python -m streamlit run data/scripts.py
# 加端口：python -m streamlit run data/scripts.py --server.port 8504
# Streamlit动不占用终端，后台运行：Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "-m streamlit run data/scripts.py --server.port 850x"
# 1）显示表格
st.dataframe(df_comments)
# 2）显示直方图
st.altair_chart(hist, width='stretch')
# 在 Streamlit 中显示饼图
st.altair_chart(pie, width='stretch')


# 在jupyter中显示结果
# 加端口：python -m notebook --port 8891
# Jupyter 后台运行：Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "-m notebook --port 8891"
hist.show()



