import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="桃園聚餐表單", page_icon="🍽️", layout="centered")

# ---------- UI 美化 ----------
st.title("🍽️ 桃園聚餐選擇表單")
st.markdown("請依序選擇日期、餐廳類型與店家，填寫後可儲存回答。")
st.markdown("---")

# 管理者密碼設定（自行修改）
ADMIN_PASSWORD = "900508"
RESPONSES_CSV = "answers.csv"

# ---------- 問卷表單 ----------
with st.form(key="response_form"):
    st.subheader("📅 選擇日期")
    date = st.date_input("請選擇聚餐日期")

    st.subheader("🍱 選擇餐廳類型")
    type_option = st.selectbox("餐廳類型", ["請選擇", "火鍋", "韓式", "義式", "其他"])

    # ----------------- 餐廳選擇 -----------------
    selected_store = ""

    # 火鍋店家
    hotpot_store = None
    if type_option == "火鍋":
        hotpot_store = st.selectbox(
            "🔥 請選擇火鍋店家",
            ["涮乃葉", "築間", "這一小鍋", "天香", "其他"]
        )
        if hotpot_store == "其他":
            hotpot_store = st.text_input("請輸入火鍋店家名稱")
        selected_store = hotpot_store

    # 韓式店家
    korean_store = None
    if type_option == "韓式":
        korean_store = st.selectbox(
            "🇰🇷 請選擇韓式店家",
            ["涓豆腐", "永和樓", "韓華園", "香港飯店", "其他"]
        )
        if korean_store == "其他":
            korean_store = st.text_input("請輸入韓式店家名稱")
        selected_store = korean_store

    # 義式店家
    italian_store = None
    if type_option == "義式":
        italian_store = st.selectbox(
            "🍝 請選擇義式店家",
            ["貳樓", "莫凡比", "亞丁尼", "其他"]
        )
        if italian_store == "其他":
            italian_store = st.text_input("請輸入義式店家名稱")
        selected_store = italian_store

    # 其他餐廳類型
    if type_option == "其他":
        selected_store = st.text_input("請輸入餐廳或店家名稱")

    st.subheader("💬 其他備註（選填）")
    comment = st.text_area("可填寫其他需求或備註", height=80)

    submit_btn = st.form_submit_button("✅ 提交")

# ---------- 提交處理 ----------
if submit_btn:
    row = {
        "date": str(date),
        "restaurant_type": type_option,
        "restaurant_name": selected_store,
        "note": comment
    }

    df_row = pd.DataFrame([row])
    if os.path.exists(RESPONSES_CSV):
        df_row.to_csv(RESPONSES_CSV, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        df_row.to_csv(RESPONSES_CSV, index=False, encoding="utf-8-sig")

    st.success("🎉 提交成功！感謝你的填寫。")
    st.balloons()
    st.json(row)

st.markdown("---")

# ---------- 管理者模式（隱藏，只有知道密碼才能看到） ----------
password = st.text_input("🔒 管理者專用密碼 (僅你知道)", type="password")
if password == ADMIN_PASSWORD:
    st.subheader("🔐 管理者區")
    if os.path.exists(RESPONSES_CSV):
        df = pd.read_csv(RESPONSES_CSV, encoding="utf-8-sig")
        st.write("總回應數：", len(df))
        st.dataframe(df)

        # 下載 CSV
        csv_bytes = open(RESPONSES_CSV, "rb").read()
        st.download_button("📥 下載 CSV", data=csv_bytes, file_name="responses.csv", mime="text/csv")

        st.markdown("#### 篩選回應")
        unique_types = df["restaurant_type"].dropna().unique().tolist()
        sel_type = st.multiselect("依餐廳類型篩選", options=unique_types)
        if sel_type:
            st.dataframe(df[df["restaurant_type"].isin(sel_type)])
    else:
        st.info("目前還沒有回應。")
