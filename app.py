import streamlit as st
import pandas as pd
import os
import random
import time
from duckduckgo_search import DDGS

# ---------- 網頁設定 ----------
st.set_page_config(
    page_title="聚餐大輪盤 (極速版)",
    page_icon="⚡",
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
    """
    只負責抓照片，不負責找餐廳，速度快且穩定
    """
    image_urls = []
    try:
        # 搜尋關鍵字：地點 + 店名 + 美食
        search_query = f"{location} {store_name} 美食"
        with DDGS() as ddgs:
            # 只抓 2 張，加速讀取
            results = list(ddgs.images(search_query, max_results=2))
            for res in results:
                image_urls.append(res['image'])
    except Exception:
        pass
    
    # 補滿預設圖
    while len(image_urls) < 2:
        image_urls.append("https://via.placeholder.com/400x300?text=Searching...")
    return image_urls

# ---------- 真實人氣資料庫 (本地端，0延遲) ----------
# 這裡我幫你整理了台北與南崁的高評價名店，你可以隨時手動擴充
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

# ---------- 初始化 Session State ----------
if 'lucky_result' not in st.session_state:
    st.session_state['lucky_result'] = None

# ==========================================
# 📝 第一部分：表單區 (支援自動填入)
# ==========================================
st.title("🍽️ 聚餐表單")
st.info("⬇️ 覺得打字很累？滑到下面用「極速轉盤」幫你決定！")

# --- 設定預設值邏輯 ---
default_type_index = 0 
default_store_val = ""

# 如果轉盤有結果，將類型強制設為 "其他"，並填入店名
if st.session_state['lucky_result']:
    default_type_index = 6 # "其他" 的 index
    default_store_val = st.session_state['lucky_result']['name']

# --- 表單開始 ---
RESPONSES_CSV = "answers.csv"
ADMIN_PASSWORD = "900508"

date = st.date_input("📅 請選擇日期")

type_options = ["請選擇", "火鍋", "韓式", "義式", "美式", "日式", "其他"]
type_option = st.selectbox("🍱 餐廳類型", type_options, index=default_type_index)

selected_store = ""

if st.session_state['lucky_result'] and type_option == "其他":
    st.success(f"⚡ 極速轉盤已填入：{default_store_val} ({st.session_state['lucky_result']['loc']})")
    selected_store = st.text_input("店家名稱", value=default_store_val)
else:
    # 一般手動選擇
    if type_option == "其他":
        selected_store = st.text_input("請輸入餐廳名稱")
    elif type_option != "請選擇":
        # 這裡簡化顯示，若要完整下拉選單可依之前的 code 加入
        selected_store = st.text_input(f"請輸入{type_option}店家名稱")

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
# ⚡ 第二部分：極速轉盤 (本地資料庫 + 雲端圖片)
# ==========================================
st.header("⚡ 極速命運轉盤")
st.write("不再轉圈圈！秒選「台北/南崁」人氣名店，並自動抓取美食照。")

placeholder = st.empty()

if st.button("🚀 幫我選！(不浪費時間版)"):
    
    # 1. 快速動畫 (純粹為了儀式感，設 1 秒即可)
    locs = list(REAL_DB.keys())
    
    for i in range(8): # 跑 8 次就好，很快
        temp_loc = random.choice(locs)
        temp_types = list(REAL_DB[temp_loc].keys())
        temp_type = random.choice(temp_types)
        temp_store = random.choice(REAL_DB[temp_loc][temp_type])
        
        placeholder.markdown(
            f"<div class='big-font'>📍 {temp_loc} | {temp_type} | {temp_store}</div>", 
            unsafe_allow_html=True
        )
        time.sleep(0.08) # 極速跳動
    
    # 2. 瞬間決定結果 (從本地 DB 抽)
    final_loc = random.choice(locs)
    final_type = random.choice(list(REAL_DB[final_loc].keys()))
    final_store = random.choice(REAL_DB[final_loc][final_type])
    
    # 3. 顯示結果並開始抓圖
    placeholder.markdown(
        f"""
        <div style='text-align:center'>
            <h3>✨ 鎖定：{final_loc} 的 <span style='color:#FF4B4B'>{final_store}</span></h3>
            <p>📸 正在抓取網路上的美食照...</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # 4. 抓圖 (這是唯一會花 1-2 秒的地方)
    imgs = fetch_image_urls(final_store, final_loc)
    
    # 5. 存檔並刷新
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

# (管理者模式略)
password = st.text_input("🔒 管理者密碼", type="password")
if password == ADMIN_PASSWORD:
    if os.path.exists(RESPONSES_CSV):
        df = pd.read_csv(RESPONSES_CSV, encoding="utf-8-sig")
        st.dataframe(df)
        st.download_button("📥 下載 CSV", open(RESPONSES_CSV, "rb"), "responses.csv")
