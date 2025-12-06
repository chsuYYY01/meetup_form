import streamlit as st
import pandas as pd
import os
import random
import time
from duckduckgo_search import DDGS  # 記得 pip install duckduckgo-search

# ---------- 網頁設定 ----------
st.set_page_config(
    page_title="聚餐表單",
    page_icon="🍽️",
    layout="centered"
)

# ---------- 自動爬蟲函式 (含快取) ----------
# 使用 Streamlit 的快取功能，抓過的圖片就不用再抓一次，避免被封鎖且加速
@st.cache_data(ttl=3600)  # 快取保留 1 小時
def fetch_image_urls(query_text, max_imgs=2):
    """
    利用 DuckDuckGo 搜尋餐廳名稱的圖片
    """
    image_urls = []
    try:
        # 搜尋關鍵字加上 "美食" 或 "菜單" 增加準確度
        search_query = f"{query_text} 美食"
        with DDGS() as ddgs:
            # 搜尋圖片，取出前 max_imgs 張
            results = list(ddgs.images(search_query, max_results=max_imgs))
            for res in results:
                image_urls.append(res['image'])
    except Exception as e:
        print(f"爬蟲發生錯誤: {e}")
        # 如果失敗，回傳一個預設的錯誤圖或空字串
        return ["https://via.placeholder.com/400x300?text=No+Image+Found"] * max_imgs
    
    # 如果找不到圖，也回傳預設圖
    if not image_urls:
        return ["https://via.placeholder.com/400x300?text=Image+Not+Found"] * max_imgs
        
    return image_urls

# ---------- 資料庫設定 (只留名稱，圖片網址改為自動抓) ----------
# 這裡依照你的需求，設定 類型 -> 區域 -> 店名
# 你可以隨意新增更多店名，不用擔心找圖的問題
RESTAURANT_DB = {
    "火鍋": [
        "涮乃葉 (南崁/台北)",
        "築間幸福鍋物 (南崁)",
        "這一小鍋 (台北)",
        "天香回味 (台北)"
    ],
    "韓式": [
        "韓華園 (台北)",
        "涓豆腐 (南崁)",
        "豚花 (南崁)",
        "永和樓 (台北)"
    ],
    "義式": [
        "Solo Pasta (台北)",
        "貳樓 Second Floor (南崁/台北)",
        "莫凡比 (南崁台茂)",
        "亞丁尼義式麵屋 (台北)"
    ],
    "美式": [
        "Everywhere burger club (台北)",
        "JK Studio (南崁)",
        "GB鮮釀餐廳 (台北)"
    ],
    "日式": [ # 新增日式
        "藏壽司 (南崁)",
        "一蘭拉麵 (台北)",
        "彌生軒 (台北)",
        "大戶屋 (南崁)"
    ]
}

# ---------- 初始化 Session State ----------
if 'lucky_type' not in st.session_state:
    st.session_state['lucky_type'] = None
if 'lucky_store' not in st.session_state:
    st.session_state['lucky_store'] = None
if 'lucky_imgs' not in st.session_state: # 新增：存抓到的圖
    st.session_state['lucky_imgs'] = []

st.title("🍽️ 聚餐選擇表單")
st.markdown("請依序選擇日期、餐廳類型與店家，填寫後提交即可。")

# ==========================================
# 🎲 選擇困難救星 (含自動爬圖)
# ==========================================
with st.expander("🎲 不知道吃什麼？點開這裡幫你決定！", expanded=True):
    st.write("點擊按鈕，系統會隨機挑選類型與人氣餐廳，並**自動搜尋該店照片**。")
    
    if st.button("🎰 啟動命運轉盤"):
        # 1. 轉盤特效
        with st.spinner('正在轉動轉盤...'):
            time.sleep(0.8) 
        
        # 2. 隨機邏輯
        r_type = random.choice(list(RESTAURANT_DB.keys()))
        r_store_name = random.choice(RESTAURANT_DB[r_type])
        
        st.session_state['lucky_type'] = r_type
        st.session_state['lucky_store'] = r_store_name
        
        # 3. 自動爬圖 (加上讀取提示)
        with st.spinner(f'正在網路上搜尋「{r_store_name}」的美食照片...'):
            imgs = fetch_image_urls(r_store_name, max_imgs=2)
            st.session_state['lucky_imgs'] = imgs

    # 顯示結果
    if st.session_state['lucky_store']:
        result_name = st.session_state['lucky_store']
        result_type = st.session_state['lucky_type']
        result_imgs = st.session_state['lucky_imgs']

        st.markdown(f"### 🎉 命運的選擇：**{result_type}**")
        st.markdown(f"#### 推薦店家：{result_name}")
        
        # 顯示抓到的圖片
        col1, col2 = st.columns(2)
        with col1:
            st.image(result_imgs[0], use_container_width=True, caption="網路搜尋結果 1")
        with col2:
            st.image(result_imgs[1], use_container_width=True, caption="網路搜尋結果 2")
            
        st.info("💡 如果照片跑不出來，可能是搜尋引擎暫時阻擋，請再試一次或直接 Google 搜尋。")

st.markdown("---")

# ---------- 檔案與密碼設定 ----------
RESPONSES_CSV = "answers.csv"
ADMIN_PASSWORD = "900508"

# ---------- 日期選擇 ----------
st.subheader("📅 選擇聚餐日期")
date = st.date_input("請選擇日期")

# ---------- 餐廳類型選擇 ----------
st.subheader("🍱 選擇餐廳類型")
type_options = ["請選擇", "火鍋", "韓式", "義式", "美式", "日式", "其他"]
type_option = st.selectbox("餐廳類型", type_options)

# ---------- 店家選擇 ----------
selected_store = ""

# 為了簡化程式碼，這裡用一個 mapping 來處理下拉選單的選項
# 你可以根據需要手動調整這裡的選項，這跟上面的 DB 可以分開，也可以連動
store_options_map = {
    "火鍋": ["涮乃葉", "築間", "這一小鍋", "天香", "其他"],
    "韓式": ["涓豆腐", "永和樓", "韓華園", "香港飯店", "其他"],
    "義式": ["貳樓", "莫凡比", "亞丁尼", "其他"],
    "美式": ["Everywhere burger club", "JK Studio", "其他"],
    "日式": ["藏壽司", "一蘭拉麵", "彌生軒", "其他"]
}

if type_option in store_options_map:
    store_list = store_options_map[type_option]
    chosen_store = st.selectbox(f"請選擇{type_option}店家", store_list)
    
    if chosen_store == "其他":
        selected_store = st.text_input(f"請輸入{type_option}店家名稱")
    else:
        selected_store = chosen_store

elif type_option == "其他":
    selected_store = st.text_input("請輸入餐廳名稱")

# 提示使用者可以填入轉盤的結果
if st.session_state['lucky_store'] and type_option == st.session_state['lucky_type']:
    st.caption(f"💡 剛剛轉盤推薦的是：**{st.session_state['lucky_store']}** (若是清單沒有，請選「其他」並手動輸入)")

# ---------- 其他備註與提交 ----------
st.subheader("💬 其他備註（選填）")
with st.form(key="response_form"):
    comment = st.text_area("可填寫其他需求或備註", height=80)
    submit_btn = st.form_submit_button("✅ 提交")

if submit_btn:
    if type_option == "請選擇":
        st.error("⚠️ 請選擇餐廳類型！")
    elif not selected_store:
        st.error("⚠️ 請確認已選擇或輸入店家名稱！")
    else:
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
        st.success("🎉 提交成功！")
        st.balloons()

# (管理者區塊保持不變，省略以節省篇幅)
