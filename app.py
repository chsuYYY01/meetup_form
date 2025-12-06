import streamlit as st
import pandas as pd
import os
from datetime import date

# ----------------------------------------------
# 頁面設定
# ----------------------------------------------
st.set_page_config(page_title="聚餐表單", page_icon="🍽️", layout="centered")

# ----------------------------------------------
# 自訂 CSS 美化
# ----------------------------------------------
st.markdown("""
    <style>
        .title {
            font-size: 34px;
            font-weight: 700;
            color: #2E86C1;
            text-align: center;
            margin-bottom: 20px;
        }
        .subtitle {
            font-size: 18px;
            color: #555;
            text-align: center;
            margin-bottom: 30px;
        }
        .card {
            background: #ffffff;
            padding: 25px 30px;
            border-radius: 16px;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------
# 標題
# ----------------------------------------------
st.markdown("<div class='title'>🍽️ 聚餐意願表單</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>請依序填寫以下資訊，提交後即可完成！</div>", unsafe_allow_html=True)

# ----------------------------------------------
# 表單卡片區塊
# ----------------------------------------------
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    # 日期
    date_selected = st.date_input("📅 請選擇日期", value=date.today())

    # 餐飲類型
    type_option = st.selectbox(
        "🍱 想吃哪種類型？",
        ["請選擇", "韓式", "火鍋", "日式"]
    )

    # 火鍋類型店家
    hotpot_store = None
    if type_option == "火鍋":
        hotpot_store = st.selectbox(
            "🔥 請選擇火鍋店家",
            ["輕井澤", "築間", "海底撈", "鼎王", "其他"]
        )

    # 韓式店家
    korean_store = None
    if type_option == "韓式":
        korean_store = st.selectbox(
            "🇰🇷 請選擇韓式店家",
            ["新麻蒲", "八色烤肉", "豆腐村", "其他"]
        )

    # 補充
    comment = st.text_area("💬 其他補充（選填）", height=100)

    # 提交按鈕
    submitted = st.button("提交")

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------
# 資料提交處理
# ----------------------------------------------
if submitted:
    data = {
        "date": [str(date_selected)],
        "type": [type_option],
        "hotpot_store": [hotpot_store],
        "korean_store": [korean_store],
        "comment": [comment]
    }

    df = pd.DataFrame(data)

    # 寫入 CSV 檔
    if os.path.exists("answers.csv"):
        df.to_csv("answers.csv", mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        df.to_csv("answers.csv", index=False, encoding="utf-8-sig")

    st.success("🎉 提交成功！感謝你的填寫")
    st.balloons()

# ----------------------------------------------
# 管理者模式（隱藏入口）
# 只有網址帶 ?admin=1 才會顯示
# 例如：http://localhost:8501/?admin=1
# ----------------------------------------------
query_params = st.query_params

if "admin" in query_params:
    st.markdown("### 🔐 管理者登入")
    password = st.text_input("請輸入管理密碼", type="password")

    if password == "900508":  # ← 你可以自行修改密碼
        st.success("登入成功（僅你能看到）")
        if os.path.exists("answers.csv"):
            df_all = pd.read_csv("answers.csv", encoding="utf-8-sig")
            st.dataframe(df_all)
        else:
            st.info("目前尚無回應資料")
    elif password != "":
        st.error("密碼錯誤")
