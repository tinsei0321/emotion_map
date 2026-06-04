# 这是一个代码联系测试
# 第一部分：测试项目为 评论 → 字典 → 列表 → dataframe 代码实践

comments = [
    "小区绿化率非常高，空气很清新！",
    "这边太吵了，楼下施工没停过",
    "商圈很方便，餐饮选择多",
    "每次路过都觉得压抑，路灯太暗",
    "公园很美，适合跑步散步"
]

# 生成空列表，准备给字典用
all_comments = []

# for循环处理评论，用snownlp进行情绪打分，并对分数进行极性判断，大于0.5为正面，小于0.5为负面，等于0.5为中性
from snownlp import SnowNLP
for i, text in enumerate(comments):
    s = SnowNLP(text).sentiments    # s = score，情绪打分
    if s > 0.5:
        polarity = "正面"
    elif s < 0.5:
        polarity = "负面"
    else:
        polarity = "中性"
    dict_comments = {
        "id": f"e{i+1:03d}",    # e001, e002, e003...
        "content": text,
        "score": round(s, 2),
        "polarity": polarity
    }

    # 将字典添加到列表中
    all_comments.append(dict_comments)

    # 将list转为dataframe
import pandas as pd
df_comments = pd.DataFrame(all_comments)


# 第二部分：对df_comments进行统计分析

import altair as alt
import streamlit as st 

# 直方图
hist = alt.Chart(df_comments).mark_bar().encode(
    x=alt.X('polarity:N', title='情绪极性'),
    y=alt.Y('count()', title='评论数量'),
    color=alt.Color('polarity:N', legend=None)
).properties(
    title='评论情绪极性分布'
)

# 在jupyter notebook中显示结果
hist.show()
