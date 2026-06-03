import streamlit as st
import pandas as pd
from snownlp import SnowNLP
import altair as alt

# ---------- 页面配置 ----------
st.set_page_config(
    page_title="评论情感分析系统",
    page_icon="💬",
    layout="wide"
)

# ---------- 标题 ----------
st.title("💬 评论情感分析系统")
st.markdown("基于 **SnowNLP** 的中文情感分析，将评论数据 → 字典 → 列表 → DataFrame，并以可视化方式展示")

# ---------- 侧边栏 ----------
with st.sidebar:
    st.header("⚙️ 设置")
    
    # 预设评论 / 自定义评论切换
    mode = st.radio("评论来源", ["使用预设评论", "自定义输入评论"])
    
    if mode == "自定义输入评论":
        user_input = st.text_area("输入评论（每行一条）", height=200)
        if user_input.strip():
            comments = [line.strip() for line in user_input.split("\n") if line.strip()]
        else:
            comments = []
    else:
        # 预设评论（来自原始脚本）
        comments = [
            "小区绿化特别好，住着很舒服",
            "这边太吵了，楼下施工没停过",
            "商圈很方便，餐饮选择多",
            "每次路过都觉得压抑，路灯太暗",
            "公园很美，适合跑步散步"
        ]
    
    analyze_btn = st.button("🚀 开始分析", type="primary", use_container_width=True)

# ---------- 主区域 ----------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 原始评论")
    df_show = pd.DataFrame({"评论内容": comments})
    st.dataframe(df_show, width='stretch', hide_index=True)

with col2:
    st.subheader("📊 统计概览")
    st.metric("评论总数", len(comments))

# ---------- 情感分析逻辑 ----------
if analyze_btn and comments:
    with st.spinner("⏳ 正在分析评论情感..."):
        all_comments = []
        
        progress_bar = st.progress(0)
        
        for i, text in enumerate(comments):
            if not text.strip():
                continue
            s = SnowNLP(text).sentiments
            if s > 0.5:
                polarity = "正面 😊"
            elif s < 0.5:
                polarity = "负面 😞"
            else:
                polarity = "中性 😐"
            
            dict_comments = {
                "id": f"e{i+1:03d}",
                "content": text,
                "score_2f": round(s, 2),
                "polarity": polarity
            }
            all_comments.append(dict_comments)
            
            progress_bar.progress((i + 1) / len(comments))
        
        # 转 DataFrame
        df_comments = pd.DataFrame(all_comments)
        
        # ---------- 显示结果 ----------
        st.success("✅ 分析完成！")
        
        # ---- 结果表格 ----
        st.subheader("📊 情感分析结果")
        
        # 用颜色标记极性
        def highlight_polarity(val):
            if "正面" in val:
                return "background-color: #d4edda; color: #155724"
            elif "负面" in val:
                return "background-color: #f8d7da; color: #721c24"
            else:
                return "background-color: #fff3cd; color: #856404"
        
        styled_df = df_comments.style.map(
            highlight_polarity, subset=["polarity"]
        )
        
        st.dataframe(styled_df, width='stretch', hide_index=True)
        
        # ---- 统计卡片 ----
        st.subheader("📈 情感分布")
        
        pos_count = len(df_comments[df_comments["polarity"].str.contains("正面")])
        neg_count = len(df_comments[df_comments["polarity"].str.contains("负面")])
        neu_count = len(df_comments[df_comments["polarity"].str.contains("中性")])
        
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("😊 正面", pos_count)
        col_b.metric("😞 负面", neg_count)
        col_c.metric("😐 中性", neu_count)
        col_d.metric("平均分", f"{df_comments['score_2f'].mean():.2f}")
        
        # ---- 可视化图表 ----
        st.subheader("📉 情感分数可视化")
        
        # 柱状图 - 每条评论的分数
        chart_data = df_comments.copy()
        chart_data["评论编号"] = chart_data["id"]
        chart_data["情感分数"] = chart_data["score_2f"]
        
        bar_chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X("评论编号:N", title="评论编号"),
            y=alt.Y("情感分数:Q", title="情感分数", scale=alt.Scale(domain=[0, 1])),
            color=alt.Color("polarity:N", title="情感极性",
                           scale=alt.Scale(
                               domain=["正面 😊", "负面 😞", "中性 😐"],
                               range=["#28a745", "#dc3545", "#ffc107"]
                           )),
            tooltip=["id", "content", "score_2f", "polarity"]
        ).properties(
            height=400,
            title="各评论情感分数"
        )
        
        st.altair_chart(bar_chart, width='stretch')
        
        # ---- 饼图 ----
        pie_data = pd.DataFrame({
            "极性": ["正面 😊", "负面 😞", "中性 😐"],
            "数量": [pos_count, neg_count, neu_count]
        })
        pie_data = pie_data[pie_data["数量"] > 0]
        
        pie_chart = alt.Chart(pie_data).mark_arc().encode(
            theta="数量:Q",
            color=alt.Color("极性:N", scale=alt.Scale(
                domain=["正面 😊", "负面 😞", "中性 😐"],
                range=["#28a745", "#dc3545", "#ffc107"]
            )),
            tooltip=["极性", "数量"]
        ).properties(
            height=300,
            title="情感极性分布"
        )
        
        col_pie1, col_pie2 = st.columns(2)
        with col_pie1:
            st.altair_chart(pie_chart, width='stretch')
        
        with col_pie2:
            # 分数分布直方图
            hist_chart = alt.Chart(chart_data).mark_bar().encode(
                x=alt.X("score_2f:Q", bin=alt.Bin(maxbins=10), title="分数区间"),
                y=alt.Y("count()", title="评论数量"),
                color=alt.Color("polarity:N", title="极性",
                               scale=alt.Scale(
                                   domain=["正面 😊", "负面 😞", "中性 😐"],
                                   range=["#28a745", "#dc3545", "#ffc107"]
                               ))
            ).properties(
                height=300,
                title="情感分数分布"
            )
            st.altair_chart(hist_chart, width='stretch')

elif analyze_btn and not comments:
    st.warning("⚠️ 请输入至少一条评论！")

# ---------- 底部说明 ----------
st.divider()
st.markdown("""
**📝 说明**
- 使用 **SnowNLP** 库进行中文情感分析，分数范围 0~1
- 分数 > 0.5 为 **正面**，< 0.5 为 **负面**，= 0.5 为 **中性**
- 支持自定义输入评论（每行一条），实时分析展示
""")


