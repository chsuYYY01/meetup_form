import streamlit as st
import pandas as pd
import os
import random
import time
from duckduckgo_search import DDGS

# ---------- 網頁設定 ----------
st.set_page_config(
    page_title="聚餐大輪盤 (連網版)",
    page_icon="🎰",
    layout="centered"
)

# ---------- CSS 美化 ----------
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        font-size: 20px;
        font-weight: bold;
        border-radius: 10px;
        background-color: #FF4B4B;
        color: white;
    }
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 10px;
    }
    .result-card {
        padding: 20px;
        border-radius: 15px;
        background-color: #f0f2f6;
        text-align: center;
        margin-top: 20px;
        border: 2px solid #FF4B4B;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------- 核心功能：網路地圖搜尋 + 抓圖 ----------
@st.cache_data(ttl=3600)
def search_random_restaurant(location, food_type):
    """
    使用 DuckDuckGo Maps 搜尋真實店家，並隨機挑選一家
    """
    query = f"{location} {food_type}"
    results = []
    
    try:
        with DDGS() as ddgs:
            # 使用 maps 搜尋，這會回傳真實的店家名稱、地址等
            # max_results 設定 20，從這 20 家裡面隨機抽一家
            places = list(ddgs.maps(query, max_results=20))
            if places:
                # 隨機挑選一家
                picked = random.choice(places)
                return {
                    "name": picked['title'],
                    "address": picked.get('address', '地址未知'),
                    "type": food_type,
                    "location": location
                }
    except Exception as e:
        print(f"地圖搜尋失敗: {e}")
        return None
    return None

@st.cache_data(ttl=3600)
def fetch_image_urls(store_name):
    """
    根據店名搜尋圖片
    """
    image_urls = []
    try:
        search_query = f"{store_name} 美食 菜單"
        with DDGS() as ddgs:
            results = list(ddgs.images(search_query, max_results=2))
            for res in results:
                image_urls.append(res['image'])
    except Exception:
        pass
    
    # 補滿預設圖，避免介面壞掉
    while len(image_urls) < 2:
        image_urls.append("https://via.placeholder.com/400x300?text=No+Image+Found")
    return image_urls

# ---------- 初始化 Session State ----------
if 'lucky_result' not in st.session_state:
    st.session_state['lucky_result'] = None

# ==========================================
# 📝 第一部分：表單區 (支援自動填入)
# ==========================================
st.title("🍽️ 聚餐表單")
st.info("⬇️ 滑到最下方使用「命運轉盤」，系統會從網路上隨機挖掘人氣餐廳！")

# --- 設定預設值邏輯 ---
default_type_index = 0 # 預設是 "請選擇" (index 0)
default_store_val = ""

# 如果轉盤有結果，將類型強制設為 "其他"，並填入店名
if st.session_state['lucky_result']:
    # "其他" 在選項列表中的 index (假設列表如下)
    # ["請選擇", "火鍋", "韓式", "義式", "美式", "日式", "其他"]
    # "其他" 是第 6 個 (index 6)
    default_type_index = 6 
    default_store_val = st.session_state['lucky_result']['name']

# --- 表單開始 ---
RESPONSES_CSV = "answers.csv"
ADMIN_PASSWORD = "900508"

date = st.date_input("📅 請選擇日期")

type_options = ["請選擇", "火鍋", "韓式", "義式", "美式", "日式", "其他"]
# 這裡使用 index 來控制預設選項
type_option = st.selectbox("🍱 餐廳類型", type_options, index=default_type_index)

# 店家名稱處理
selected_store = ""

# 如果是轉盤轉出來的，且目前選的是 "其他"，顯示提示並填入值
if st.session_state['lucky_result'] and type_option == "其他":
    st.success(f"💡 命運轉盤結果已填入：{default_store_val}")
    selected_store = st.text_input("店家名稱", value=default_store_val)
else:
    # 這裡保留原本的手動選擇邏輯，但當使用者選 "其他" 時給予輸入框
    store_map = {
        "火鍋": ["涮乃葉", "築間", "這一小鍋", "天香", "其他"],
        "韓式": ["涓豆腐", "永和樓", "韓華園", "香港飯店", "其他"],
        "義式": ["貳樓", "莫凡比", "亞丁尼", "其他"],
        "美式": ["Everywhere burger club", "JK Studio", "其他"],
        "日式": ["藏壽司", "一蘭拉麵", "彌生軒", "其他"]
    }
    
    if type_option in store_map:
        s_list = store_map[type_option]
        s_opt = st.selectbox(f"請選擇{type_option}店家", s_list)
        selected_store = st.text_input(f"請輸入{type_option}名稱") if s_opt == "其他" else s_opt
    elif type_option == "其他":
        selected_store = st.text_input("請輸入餐廳名稱")
    else:
        selected_store = "" # 請選擇狀態

with st.form(key="response_form"):
    comment = st.text_area("💬 其他備註", height=80)
    submit_btn = st.form_submit_button("✅ 提交表單")

if submit_btn:
    if type_option == "請選擇":
        st.error("⚠️ 請選擇餐廳類型！")
    elif not selected_store:
        st.error("⚠️ 請確認店家名稱！")
    else:
        row = {"date": str(date), "type": type_option, "store": selected_store, "note": comment}
        df_row = pd.DataFrame([row])
        mode = "a" if os.path.exists(RESPONSES_CSV) else "w"
        header = not os.path.exists(RESPONSES_CSV)
        df_row.to_csv(RESPONSES_CSV, mode=mode, header=header, index=False, encoding="utf-8-sig")
        st.balloons()
        st.success("提交成功！")

st.markdown("---")

# ==========================================
# 🎰 第二部分：真・連網命運轉盤
# ==========================================
st.header("🎲 真・命運轉盤 (連線搜尋中...)")
st.write("系統將直接搜尋 Google Maps/DuckDuckGo 資料庫，找出真實存在的餐廳。")

placeholder = st.empty()

# 設定要抽籤的類型與地點池
LOCATIONS = ["台北", "南崁"]
FOOD_TYPES = ["火鍋", "韓式料理", "義式餐廳", "美式漢堡", "日式燒肉", "拉麵", "泰式料理"]

if st.button("🚀 啟動引擎，幫我找好吃的！"):
    
    # 1. 第一階段：隨機決定「地點」與「類型」
    # 動畫效果：快速跳動類型
    target_loc = ""
    target_type = ""
    
    for i in range(10):
        target_loc = random.choice(LOCATIONS)
        target_type = random.choice(FOOD_TYPES)
        placeholder.markdown(
            f"<div class='big-font'>📍 {target_loc} | 🍱 {target_type}</div>", 
            unsafe_allow_html=True
        )
        time.sleep(0.1)
    
    # 2. 第二階段：顯示「正在連網搜尋」
    placeholder.markdown(
        f"""
        <div style='text-align:center'>
            <h3>🔒 鎖定目標：{target_loc} 的 {target_type}</h3>
            <p>📡 正在連線搜尋當地評價最高的餐廳清單...</p>
            <p>(這可能需要 3~5 秒，請耐心等待)</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # 3. 實際執行網路搜尋 (這步最花時間)
    # 我們呼叫 maps 搜尋，這會去抓真實資料
    found_place = search_random_restaurant(target_loc, target_type)
    
    if found_place:
        # 4. 搜尋該店家的圖片
        placeholder.markdown(f"<p style='text-align:center'>📸 找到店家「{found_place['name']}」，正在抓取照片...</p>", unsafe_allow_html=True)
        imgs = fetch_image_urls(found_place['name'])
        
        # 5. 存入 Session 並刷新
        st.session_state['lucky_result'] = {
            "name": found_place['name'],
            "type": target_type, # 這裡存原本的類型名稱供參考
            "imgs": imgs,
            "address": found_place['address']
        }
        st.rerun()
    else:
        st.error("搜尋超時或找不到餐廳，請再試一次！")

# --- 顯示結果卡片 ---
if st.session_state['lucky_result']:
    res = st.session_state['lucky_result']
    
    placeholder.empty()
    
    st.markdown(f"""
    <div class="result-card">
        <h3>🎉 命運指定：{res['name']}</h3>
        <p>📍 地址：{res['address']}</p>
        <p>☝️ <b>表單已自動切換為「其他」並填入此店名！</b></p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.image(res['imgs'][0], use_container_width=True, caption="網路搜尋結果 1")
    with col2:
        st.image(res['imgs'][1], use_container_width=True, caption="網路搜尋結果 2")

st.markdown("---")

# ---------- 管理者模式 (保持不變) ----------
password = st.text_input("🔒 管理者密碼", type="password")
if password == ADMIN_PASSWORD:
    if os.path.exists(RESPONSES_CSV):
        df = pd.read_csv(RESPONSES_CSV, encoding="utf-8-sig")
        st.dataframe(df)
        st.download_button("📥 下載 CSV", open(RESPONSES_CSV, "rb"), "responses.csv")
