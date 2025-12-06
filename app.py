import streamlit as st
import pandas as pd
import os
import random
import time
from duckduckgo_search import DDGS

# ---------- 網頁設定 ----------
st.set_page_config(
    page_title="聚餐大輪盤 (真實地址版)",
    page_icon="📍",
    layout="centered"
)

# ---------- CSS 美化 (Dark Mode 優化 + 地址卡片) ----------
st.markdown("""
    <style>
    /* 全局按鈕 */
    .stButton>button {
        width: 100%;
        font-size: 20px;
        font-weight: bold;
        border-radius: 12px;
        background: linear-gradient(135deg, #FF4B4B, #FF914D);
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 75, 75, 0.6);
    }
    
    /* 轉盤跳動字體 */
    .big-font {
        font-size: 26px !important;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 5px;
    }
    .small-addr {
        font-size: 16px;
        color: #aaaaaa;
        text-align: center;
        margin-bottom: 15px;
    }
    
    /* 結果卡片 (Glassmorphism) */
    .result-card {
        padding: 25px;
        border-radius: 16px;
        background-color: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        margin-top: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        color: #ffffff;
    }
    .result-card h2 {
        color: #FF4B4B !important;
        margin: 0;
        font-size: 32px;
    }
    .result-card .addr-text {
        color: #FFD700 !important; /* 金色地址 */
        font-size: 20px;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    
    /* Google Maps Link */
    .map-link {
        display: inline-block;
        text-decoration: none;
        background-color: #4285F4;
        color: white !important;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 14px;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------- 只有抓圖才連網 (速度快) ----------
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
        image_urls.append("https://via.placeholder.com/400x300/333333/FFFFFF?text=Loading...")
    return image_urls

# ---------- 資料庫 1：真實驗證清單 (含地址) ----------
# 這裡都是真實存在的店，如果店家倒了，可以在這裡手動更新
VERIFIED_DB = {
    "台北": {
        "火鍋": [
            {"name": "詹記麻辣火鍋 敦南店", "addr": "台北市大安區和平東路三段60號"},
            {"name": "橘色涮涮屋 一館", "addr": "台北市大安區大安路一段135號B1"},
            {"name": "雞湯大叔 民生店", "addr": "台北市中山區民生東路二段131號"},
            {"name": "青花驕麻辣鍋 台北中山北店", "addr": "台北市中山區中山北路一段137號"}
        ],
        "韓式": [
            {"name": "韓華園", "addr": "台北市中山區民權東路三段47號"},
            {"name": "料韓男 (復興店)", "addr": "台北市大安區復興南路一段107巷5弄13號"},
            {"name": "輪流請客", "addr": "台北市內湖區瑞光路589號"}
        ],
        "義式": [
            {"name": "Solo Pasta", "addr": "台北市大安區安和路一段29-1號"},
            {"name": "Cin Cin Osteria 請請義大利餐廳", "addr": "台北市松山區慶城街16巷16號"},
            {"name": "Salt & Stone", "addr": "台北市信義區市府路45號4樓 (101大樓)"}
        ],
        "美式": [
            {"name": "Everywhere burger club", "addr": "台北市大安區光復南路420巷21號"},
            {"name": "Butcher by Lanpengyou", "addr": "台北市信義區基隆路二段87號"}
        ],
        "日式": [
            {"name": "麵屋一燈", "addr": "台北市中山區南京東路一段29號"},
            {"name": "合點壽司 華山店", "addr": "台北市中正區八德路一段1號"},
            {"name": "上引水產", "addr": "台北市中山區民族東路410巷2弄18號"}
        ],
        "燒肉": [
            {"name": "大腕燒肉", "addr": "台北市中山區敬業二路199號5樓"},
            {"name": "胡同燒肉1號店", "addr": "台北市大安區敦化南路一段161巷17號"}
        ]
    },
    "南崁": {
        "火鍋": [
            {"name": "築間幸福鍋物 桃園南崁店", "addr": "桃園市蘆竹區中正路323號2樓"},
            {"name": "肉多多火鍋 桃園南崁店", "addr": "桃園市蘆竹區南崁路265號3樓"},
            {"name": "天香回味 桃園南崁店", "addr": "桃園市蘆竹區南山路一段52號"}
        ],
        "韓式": [
            {"name": "豚花敦", "addr": "桃園市蘆竹區洛陽街8號"},
            {"name": "韓大叔正宗韓式烤肉", "addr": "桃園市蘆竹區南崁路一段8號"},
            {"name": "大邱骨道", "addr": "桃園市蘆竹區中正路306號"}
        ],
        "義式": [
            {"name": "JK Studio 義法餐廳", "addr": "桃園市蘆竹區新南路一段16號"},
            {"name": "NiNi 尼尼義大利餐廳", "addr": "桃園市蘆竹區南竹路二段313-1號"}
        ],
        "美式": [
            {"name": "TGI FRIDAYS 台茂餐廳", "addr": "桃園市蘆竹區南崁路一段112號 (台茂1F)"},
            {"name": "GB鮮釀餐廳", "addr": "桃園市蘆竹區南崁路一段112號 (台茂1F)"}
        ],
        "日式": [
            {"name": "藏壽司 桃園南崁店", "addr": "桃園市蘆竹區中正路306號"},
            {"name": "Magic Touch 点爭鮮", "addr": "桃園市蘆竹區南崁路一段112號 (台茂5F)"}
        ],
        "燒肉": [
            {"name": "山奧屋無煙燒肉", "addr": "桃園市蘆竹區南崁路一段7號"},
            {"name": "燒肉道", "addr": "桃園市蘆竹區桃園街112號"}
        ]
    }
}

# ---------- 資料庫 2：手動下拉清單 ----------
STORE_MAP_MANUAL = {
    "火鍋": ["涮乃葉", "築間", "這一小鍋", "天香", "其他"],
    "韓式": ["涓豆腐", "永和樓", "韓華園", "香港飯店", "其他"],
    "義式": ["貳樓", "莫凡比", "亞丁尼", "其他"],
    "美式": ["Everywhere burger club", "JK Studio", "其他"],
    "日式": ["藏壽司", "一蘭拉麵", "彌生軒", "其他"],
    "燒肉": ["原燒", "乾杯", "其他"]
}

# ---------- 初始化 Session State ----------
if 'lucky_result' not in st.session_state:
    st.session_state['lucky_result'] = None

# ==========================================
# 📝 第一部分：表單區
# ==========================================
st.title("🍽️ 聚餐表單")
st.info("⬇️ 點擊最下方的「極速轉盤」，系統會選出真實店家與地址！")

# --- 1. 計算預設值 ---
type_options_list = ["請選擇", "火鍋", "韓式", "義式", "美式", "日式", "燒肉", "其他"]
default_type_index = 0 
default_store_val = ""
is_lucky_mode = False

if st.session_state['lucky_result']:
    lucky_data = st.session_state['lucky_result']
    lucky_type = lucky_data['type']
    
    if lucky_type in type_options_list:
        default_type_index = type_options_list.index(lucky_type)
        default_store_val = lucky_data['name']
        is_lucky_mode = True
    else:
        default_type_index = type_options_list.index("其他")
        default_store_val = lucky_data['name']
        is_lucky_mode = True

# --- 表單開始 ---
RESPONSES_CSV = "answers.csv"
ADMIN_PASSWORD = "900508"

date = st.date_input("📅 請選擇日期")
type_option = st.selectbox("🍱 餐廳類型", type_options_list, index=default_type_index)
selected_store = ""

# --- 2. 智慧輸入框邏輯 ---
if is_lucky_mode and type_option == st.session_state['lucky_result']['type']:
    # 這裡顯示提示，包含店名和地址
    lucky_info = st.session_state['lucky_result']
    st.success(f"📍 已自動填入：{lucky_info['name']}")
    st.caption(f"地址：{lucky_info['addr']}")
    selected_store = st.text_input("店家名稱", value=default_store_val)

elif type_option in STORE_MAP_MANUAL:
    store_list = STORE_MAP_MANUAL[type_option]
    chosen_store = st.selectbox(f"請選擇{type_option}店家", store_list)
    if chosen_store == "其他":
        selected_store = st.text_input(f"請輸入{type_option}店家名稱")
    else:
        selected_store = chosen_store
elif type_option == "其他":
    selected_store = st.text_input("請輸入餐廳名稱")
else:
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
# ⚡ 第二部分：極速轉盤 (顯示真實地址)
# ==========================================
st.header("⚡ 極速命運轉盤")
st.write("點擊按鈕，隨機挑選一家真實存在的超人氣餐廳！")

placeholder = st.empty()

if st.button("🚀 啟動命運引擎"):
    locs = list(VERIFIED_DB.keys())
    
    # 1. 轉盤動畫
    for i in range(10):
        t_loc = random.choice(locs)
        t_types = list(VERIFIED_DB[t_loc].keys())
        t_type = random.choice(t_types)
        # 暫時隨機取一家做動畫
        t_store_data = random.choice(VERIFIED_DB[t_loc][t_type])
        
        placeholder.markdown(f"""
            <div class='big-font'>{t_loc} | {t_type}</div>
            <div class='small-addr'>{t_store_data['name']}</div>
        """, unsafe_allow_html=True)
        time.sleep(0.08)
    
    # 2. 決定最終結果
    f_loc = random.choice(locs)
    f_type = random.choice(list(VERIFIED_DB[f_loc].keys()))
    f_store_data = random.choice(VERIFIED_DB[f_loc][f_type])
    
    f_name = f_store_data['name']
    f_addr = f_store_data['addr']
    
    placeholder.markdown(f"""
        <div style='text-align:center'>
            <h3>✨ 鎖定：{f_name}</h3>
            <p>📍 {f_addr}</p>
            <p>📸 正在抓取照片...</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 3. 抓圖
    imgs = fetch_image_urls(f_name, f_loc)
    
    # 4. 存檔並刷新
    st.session_state['lucky_result'] = {
        "name": f_name,
        "addr": f_addr,
        "type": f_type,
        "loc": f_loc,
        "imgs": imgs
    }
    st.rerun()

# --- 顯示結果卡片 ---
if st.session_state['lucky_result']:
    res = st.session_state['lucky_result']
    placeholder.empty()
    
    # 產生 Google Maps 連結
    map_url = f"https://www.google.com/maps/search/?api=1&query={res['addr']}"
    
    st.markdown(f"""
    <div class="result-card">
        <h2>{res['name']}</h2>
        <div class="addr-text">📍 {res['addr']}</div>
        <p>類型：{res['type']} | 地區：{res['loc']}</p>
        <a href="{map_url}" target="_blank" class="map-link">🗺️ Google Maps 導航</a>
        <br><br>
        <p style="color:#ffffffaa; font-size:14px;">☝️ 表單已自動填好，可以直接提交！</p>
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
