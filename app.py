import streamlit as st
import pandas as pd
import os

st.title("🍽️ 桃園聚餐表單")

RESPONSES_CSV = "answers.csv"
ADMIN_PASSWORD = "900508"

# ---------- 餐廳類型選擇 ----------
type_option = st.selectbox("🍱 選擇餐廳類型", ["請選擇", "火鍋", "韓式", "義式", "其他"])

# ---------- 店家選擇（立即顯示） ----------
selected_store = ""
if type_option == "火鍋":
    hotpot_store = st.selectbox(
        "🔥 請選擇火鍋店家",
        ["涮乃葉", "築間", "這一小鍋", "天香", "其他"]
    )
    if hotpot_store == "其他":
        hotpot_store = st.text_input("請輸入火鍋店家名稱")
    selected_store = hotpot_store

elif type_option == "韓式":
    korean_store = st.selectbox(
        "🇰🇷 請選擇韓式店家",
        ["涓豆腐", "永和樓", "韓華園", "香港飯店", "其他"]
    )
    if korean_store == "其他":
        korean_store = st.text_input("請輸入韓式店家名稱")
    selected_store = korean_store

elif type_option == "義式":
    italian_store = st.selectbox(
        "🍝 請選擇義式店家",
        ["貳樓", "莫凡比", "亞丁尼", "其他"]
    )
    if italian_store == "其他":
        italian_store = st.text_input("請輸入義式店家名稱")
    selected_store = italian_store

elif type_option == "其他":
    selected_store = st.text_input("請輸入餐廳名稱")

# ---------- 其他備註 + 提交 ----------
with st.form(key="response_form"):
    comment = st.text_area("💬 其他備註（選填）", height=80)
    submit_btn = st.form_submit_button("✅ 提交")

if submit_btn:
    row = {
        "restaurant_type": type_option,
        "restaurant_name": selected_store,
        "note": comment
    }
    df_row = pd.DataFrame([row])
    if os.path.exists(RESPONSES_CSV):
        df_row.to_csv(RESPONSES_CSV, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        df_row.to_csv(RESPONSES_CSV, index=False, encoding="utf-8-sig")
    st.success("🎉 提交成功！")
    st.balloons()
