from snownlp import SnowNLP
import pandas as pd
import altair as alt

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

pie = alt.Chart(df_count).mark_arc().encode(
    theta=alt.Theta(field="count:Q", type="quantitative"),
    color=alt.Color(field="polarity", type="nominal")
).properties(
    title='评论情绪极性分布'
)

hist.show()
pie.show()


# python -m notebook --port 8891
