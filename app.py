import streamlit as st
import pandas as pd
import os
import random
import time
from duckduckgo_search import DDGS

# ---------- 網頁設定 ----------
st.set_page_config(
    page_title="聚餐大輪盤 (完整版)",
    page_icon="🍲",
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

# ---------- 只有抓圖才連網 (速度快很多) ----------
@st.cache_data(ttl=3600)
def fetch_image_urls(store_name, location):
    image_urls = []
    try:
        search_query = f"{location} {store_name} 美食"
        with DDGS() as ddgs:
            results = list(ddgs.images(search_query, max_results=2))
            for res in results:
                image_urls.append(res['image'])
    except Exception:
        pass
    while len(image_urls) < 2:
        image_urls.append("https://via.placeholder.com/400x300?text=Searching...")
    return image_urls

# ---------- 資料庫 1：給「命運轉盤」用的 (包含真實人氣店) ----------
REAL_DB = {
    "台北": {
        "火鍋": ["詹記麻辣火鍋", "橘色涮涮屋", "這一鍋", "青花驕", "雞湯大叔"],
        "韓式": ["韓華園", "料韓男", "Soban 小班韓式料理", "輪流請客"],
        "義式": ["Solo Pasta", "Salt & Stone", "Cin Cin Osteria 請請義大利餐廳", "螺絲瑪莉"],
        "美式": ["Everywhere burger club", "Butcher by Lanpengyou", "Big Al's Burgers"],
        "日式": ["麵屋一燈", "金子半之助", "上引水產", "合點壽司"],
        "燒肉": ["胡同燒肉", "大腕燒肉", "乾杯燒肉", "路易奇電力公司"]
    },
    "南崁": {
        "火鍋": ["築間幸福鍋物", "肉多多火鍋", "天香回味", "六扇門"],
        "韓式": ["豚花敦", "韓大叔", "大邱骨道", "韓食屋"],
        "義式": ["JK Studio", "托斯卡尼尼", "NiNi 尼尼義大利餐廳"],
        "美式": ["GB鮮釀餐廳 (台茂)", "TGI FRIDAYS (台茂)"],
        "日式": ["藏壽司", "大戶屋", "Magic Touch 点爭鮮"],
        "燒肉": ["山奧屋無煙燒肉", "我!就厲害", "燒肉道"]
    }
}

# ---------- 資料庫 2：給「手動選單」用的下拉選項 ----------
# 這是你原本希望保留的選項
STORE_MAP_MANUAL = {
    "火鍋": ["涮乃葉", "築間", "這一小鍋", "天香", "其他"],
    "韓式": ["涓豆腐", "永和樓", "韓華園", "香港飯店", "其他"],
    "義式": ["貳樓", "莫凡比", "亞丁尼", "其他"],
    "美式": ["Everywhere burger club", "JK Studio", "其他"],
    "日式": ["藏壽司", "一蘭拉麵", "彌生軒", "其他"]
}

# ---------- 初始化 Session State ----------
if 'lucky_result' not in st.session_state:
    st.session_state['lucky_result'] = None

# ==========================================
# 📝 第一部分：表單區 (修復了手動選單！)
# ==========================================
st.title("🍽️ 聚餐表單")
st.info("⬇️ 覺得打字很累？滑到下面用「極速轉盤」幫你決定！")

# --- 設定預設值邏輯 ---
default_type_index = 0 
default_store_val = ""
is_from_lucky = False

# 如果轉盤有結果，我們把預設類型設為 "其他" (Index 6)，並準備填入店名
if st.session_state['lucky_result']:
    default_type_index = 6 
    default_store_val = st.session_state['lucky_result']['name']
    is_from_lucky = True

# --- 表單開始 ---
RESPONSES_CSV = "answers.csv"
ADMIN_PASSWORD = "900508"

date = st.date_input("📅 請選擇日期")

# 這裡很重要：如果使用者自己去改了類型（例如從「其他」改回「火鍋」），我們就不應該再強制填入轉盤的結果
type_options = ["請選擇", "火鍋", "韓式", "義式", "美式", "日式", "其他"]
type_option = st.selectbox("🍱 餐廳類型", type_options, index=default_type_index)

selected_store = ""

# --- 核心邏輯修正 ---

# 情況 A：目前選的是「其他」，且轉盤有結果 -> 自動填入轉盤店名
if type_option == "其他" and is_from_lucky:
    st.success(f"⚡ 極速轉盤推薦：{default_store_val} ({st.session_state['lucky_result']['loc']})")
    selected_store = st.text_input("店家名稱", value=default_store_val)

# 情況 B：使用者手動選了某個類型 (且有定義在 STORE_MAP_MANUAL 裡) -> 顯示下拉選單
elif type_option in STORE_MAP_MANUAL:
    store_list = STORE_MAP_MANUAL[type_option]
    chosen_store = st.selectbox(f"請選擇{type_option}店家", store_list)
    
    if chosen_store == "其他":
        selected_store = st.text_input(f"請輸入{type_option}店家名稱")
    else:
        selected_store = chosen_store

# 情況 C：選了「其他」但不是轉盤來的 -> 一般手動輸入
elif type_option == "其他":
    selected_store = st.text_input("請輸入餐廳名稱")

else:
    # 這裡處理 "請選擇" 的狀態
    selected_store = ""

# --- 提交按鈕 ---
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
# ⚡ 第二部分：極速轉盤 (保留不變)
# ==========================================
st.header("⚡ 極速命運轉盤")
st.write("不再轉圈圈！秒選「台北/南崁」人氣名店，並自動抓取美食照。")

placeholder = st.empty()

if st.button("🚀 幫我選！(不浪費時間版)"):
    # 1. 動畫
    locs = list(REAL_DB.keys())
    for i in range(8):
        temp_loc = random.choice(locs)
        temp_types = list(REAL_DB[temp_loc].keys())
        temp_type = random.choice(temp_types)
        temp_store = random.choice(REAL_DB[temp_loc][temp_type])
        placeholder.markdown(f"<div class='big-font'>📍 {temp_loc} | {temp_type} | {temp_store}</div>", unsafe_allow_html=True)
        time.sleep(0.08)
    
    # 2. 結果
    final_loc = random.choice(locs)
    final_type = random.choice(list(REAL_DB[final_loc].keys()))
    final_store = random.choice(REAL_DB[final_loc][final_type])
    
    placeholder.markdown(f"""
        <div style='text-align:center'>
            <h3>✨ 鎖定：{final_loc} 的 <span style='color:#FF4B4B'>{final_store}</span></h3>
            <p>📸 正在抓取網路上的美食照...</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 3. 抓圖
    imgs = fetch_image_urls(final_store, final_loc)
    
    # 4. 存檔並刷新
    st.session_state['lucky_result'] = {
        "name": final_store,
        "type": final_type,
        "loc": final_loc,
        "imgs": imgs
    }
    st.rerun()

# --- 顯示結果卡片 ---
if st.session_state['lucky_result']:
    res = st.session_state['lucky_result']
    placeholder.empty()
    
    st.markdown(f"""
    <div class="result-card">
        <h3>🎉 推薦去吃：{res['name']}</h3>
        <p>📍 地點：{res['loc']} ({res['type']})</p>
        <p>☝️ <b>表單已自動填好囉！</b></p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.image(res['imgs'][0], use_container_width=True, caption="網路圖片 1")
    with col2:
        st.image(res['imgs'][1], use_container_width=True, caption="網路圖片 2")

st.markdown("---")

# (管理者模式保持不變)
password = st.text_input("🔒 管理者密碼", type="password")
if password == ADMIN_PASSWORD:
    if os.path.exists(RESPONSES_CSV):
        df = pd.read_csv(RESPONSES_CSV, encoding="utf-8-sig")
        st.dataframe(df)
        st.download_button("📥 下載 CSV", open(RESPONSES_CSV, "rb"), "responses.csv")
