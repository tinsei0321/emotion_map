from snownlp import SnowNLP
import pandas as pd
import altair as alt

comments = [
    "小区绿化特别好，住着很舒服",
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

df_comments = pd.DataFrame(all_comments)

hist = alt.Chart(df_comments).mark_bar().encode(
    x=alt.X('polarity:N', title='情感极性'),
    y=alt.Y('count()', title='评论数量'),
    color=alt.Color('polarity:N', legend=None)
).properties(
    title='评论情感极性分布'
)

hist  # ← 直接写变量名，Jupyter 会自动显示图表