import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="聚餐表單", page_icon="🍽️")

st.title("🍽️ 聚餐調查表單")

st.write("請依序填寫以下問題，提交後你的回答會自動記錄。")

# --- 問題 1：選日期 ---
date = st.date_input("📅 請選擇日期")


# --- 問題 2：餐廳類型 ---
type_option = st.selectbox(
    "🍱 想吃哪種類型？",
    ["請選擇", "韓式", "火鍋", "日式"]
)

# --- 如果選火鍋，顯示火鍋店 ---
hotpot_store = None
if type_option == "火鍋":
    hotpot_store = st.selectbox(
        "🔥 請選擇火鍋店家",
        ["輕井澤", "老先覺", "鼎王", "其他"]
    )

# --- 如果選韓式，顯示韓式店 ---
korean_store = None
if type_option == "韓式":
    korean_store = st.selectbox(
        "🇰🇷 請選擇韓式店家",
        ["新麻蒲", "八色烤肉", "豆腐村", "其他"]
    )

# --- 其他補充 ---
comment = st.text_area("💬 想補充什麼嗎？（選填）")


# --- 按提交 ---
if st.button("提交"):
    # 建立資料
    data = {
        "date": [str(date)],
        "type": [type_option],
        "hotpot_store": [hotpot_store],
        "korean_store": [korean_store],
        "comment": [comment]
    }

    df = pd.DataFrame(data)

    # 寫入 CSV（追加模式）
    if os.path.exists("answers.csv"):
        df.to_csv("answers.csv", mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        df.to_csv("answers.csv", index=False, encoding="utf-8-sig")

    st.success("🎉 提交成功！感謝你的填寫。")
    st.balloons()


# --- 管理端：查看所有回應 ---
st.divider()
st.subheader("🔐 管理者區（可選）")
password = st.text_input("管理者密碼", type="password")

if password == "admin123":
    st.success("已進入管理者模式")

    if os.path.exists("answers.csv"):
        df = pd.read_csv("answers.csv", encoding="utf-8-sig")
        st.dataframe(df)
    else:
        st.info("目前還沒有任何回應。")
else:
    st.info("如需查看回應，請輸入管理密碼。（預設：admin123）")
