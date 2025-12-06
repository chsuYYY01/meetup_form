import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="桃園聚餐表單", page_icon="🍽️", layout="centered")

# ---------- UI 美化 ----------
st.title("🍽️ 桃園聚餐選擇表單")
st.markdown("請依序選擇日期、餐廳類型與店家，填寫後可儲存回答。")
st.markdown("---")

# ---------- 餐廳資料 ----------
STORE_LISTS = {
    "火鍋": [
        "輕井澤(台茂店)", "老先覺(南崁店)", "鼎王(台茂店)",
        "肉多多火鍋(南崁店)", "石二鍋(台茂店)"
    ],
    "韓式": [
        "新麻蒲(台茂店)", "八色烤肉(南崁店)", "豆腐村(台茂店)",
        "韓舍韓國烤肉(南崁店)", "姜虎東白丁(台茂店)"
    ],
    "義式": [
        "莫凡彼義式餐廳(台茂店)", "陶板屋義式(南崁店)", "Trattoria義大利餐廳(台茂店)",
        "La Festa義式料理(南崁店)", "義饗食堂(台茂店)"
    ]
}

ADMIN_PASSWORD = "admin123"  # 管理者密碼，可自行更改
RESPONSES_CSV = "answers.csv"

# ---------- 問卷表單 ----------
with st.form(key="response_form"):
    st.subheader("📅 選擇日期")
    date = st.date_input("請選擇聚餐日期")

    st.subheader("🍱 選擇餐廳類型")
    type_option = st.selectbox("餐廳類型", ["請選擇"] + list(STORE_LISTS.keys()) + ["其他"])

    selected_store = ""
    if type_option in STORE_LISTS:
        st.subheader("🏠 選擇店家")
        col1, col2 = st.columns(2)
        with col1:
            selected_store = st.selectbox("請選擇店家", STORE_LISTS[type_option] + ["其他/手動輸入"])
        with col2:
            if selected_store == "其他/手動輸入":
                selected_store = st.text_input("手動輸入店家名稱")
    elif type_option == "其他":
        selected_store = st.text_input("請輸入想吃的餐廳或店家名稱")

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

# ---------- 管理者模式（完全隱藏，只有輸入密碼才會顯示） ----------
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
