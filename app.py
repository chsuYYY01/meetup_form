import streamlit as st
import pandas as pd
import os
import random
import time
from duckduckgo_search import DDGS

# ---------- 網頁設定 ----------
st.set_page_config(
    page_title="聚餐大輪盤",
    page_icon="🍲",
    layout="centered"
)

# ---------- CSS 美化 (Dark Mode 優化) ----------
st.markdown("""
    <style>
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
    .result-card h2 { color: #FF4B4B !important; margin: 0; font-size: 32px; }
    .result-card .addr-text { color: #FFD700 !important; font-size: 20px; font-weight: bold; margin-top: 10px; margin-bottom: 20px; }
    .map-link {
        display: inline-block; text-decoration: none; background-color: #4285F4;
        color: white !important; padding: 8px 16px; border-radius: 20px; font-size: 14px; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------- 只有抓圖才連網 ----------
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
        image_urls.append("https://via.placeholder.com/400x300/333333/FFFFFF?text=Searching...")
    return image_urls

# ---------- 資料庫處理函式 ----------
def load_db_from_csv(csv_path_or_file):
    try:
        df = pd.read_csv(csv_path_or_file)
        required = {'地區', '類型', '店名', '地址'}
        if not required.issubset(df.columns):
            return None, "CSV 缺少必要欄位 (地區, 類型, 店名, 地址)"
        
        new_db = {}
        for _, row in df.iterrows():
            loc = str(row['地區']).strip()
            rtype = str(row['類型']).strip()
            name = str(row['店名']).strip()
            addr = str(row['地址']).strip()
            
            if loc not in new_db: new_db[loc] = {}
            if rtype not in new_db[loc]: new_db[loc][rtype] = []
            new_db[loc][rtype].append({"name": name, "addr": addr})
        return new_db, None
    except Exception as e:
        return None, str(e)

# ---------- 預設的手動選單 (這裡保留你的舊設定) ----------
STORE_MAP_MANUAL = {
    "火鍋": ["涮乃葉", "築間", "這一小鍋", "天香", "其他"],
    "韓式": ["涓豆腐", "永和樓", "韓華園", "香港飯店", "其他"],
    "義式": ["貳樓", "莫凡比", "亞丁尼", "其他"],
    "美式": ["Everywhere burger club", "JK Studio", "其他"],
    "日式": ["藏壽司", "一蘭拉麵", "彌生軒", "其他"],
    "燒肉": ["原燒", "乾杯", "其他"]
}

# ---------- 預設的備用轉盤資料 (萬一沒 CSV 時用) ----------
DEFAULT_BACKUP_DB = {
    "台北": {"火鍋": [{"name": "詹記麻辣火鍋", "addr": "台北市大安區"}]},
    "南崁": {"火鍋": [{"name": "築間幸福鍋物", "addr": "桃園市蘆竹區"}]}
}

# ---------- 初始化 Session State ----------
if 'lucky_result' not in st.session_state:
    st.session_state['lucky_result'] = None

# ==========================================
# 📂 資料來源設定 (GitHub 部署用)
# ==========================================
st.sidebar.header("📂 資料來源")
uploaded_file = st.sidebar.file_uploader("上傳清單 (CSV)", type=["csv"])
LOCAL_CSV = "my_restaurants.csv"
active_db = {}
source_msg = ""

# 載入邏輯：上傳 > 本地CSV > 備用
if uploaded_file:
    db, err = load_db_from_csv(uploaded_file)
    if db:
        active_db = db
        source_msg = "目前使用：**使用者上傳清單**"
    else:
        st.sidebar.error(f"錯誤: {err}")
        active_db = DEFAULT_BACKUP_DB
elif os.path.exists(LOCAL_CSV):
    db, err = load_db_from_csv(LOCAL_CSV)
    if db:
        active_db = db
        source_msg = "目前使用：**我的口袋名單 (預設)**"
    else:
        active_db = DEFAULT_BACKUP_DB
        source_msg = "⚠️ 預設 CSV 讀取失敗"
else:
    active_db = DEFAULT_BACKUP_DB
    source_msg = "目前使用：**系統備用範例**"

st.session_state['active_db'] = active_db

# ==========================================
# 📝 主畫面
# ==========================================
st.title("🍽️ 聚餐表單")
st.caption(f"🎯 {source_msg}")

# --- 計算下拉選單的「類型」 ---
# 我們把「手動選單的 Key」跟「CSV 裡的類型」合併，這樣才不會漏掉
current_db_types = set()
for loc in st.session_state['active_db']:
    current_db_types.update(st.session_state['active_db'][loc].keys())

manual_types = set(STORE_MAP_MANUAL.keys())
all_types = sorted(list(manual_types | current_db_types), key=lambda x: (x=="其他", x=="請選擇", x))

if "請選擇" not in all_types: all_types.insert(0, "請選擇")
if "其他" in all_types: all_types.remove("其他"); all_types.append("其他")

# --- 處理轉盤預設值 ---
default_type_index = 0 
default_store_val = ""
is_lucky_mode = False

if st.session_state['lucky_result']:
    lucky_data = st.session_state['lucky_result']
    # 嘗試對應類型
    if lucky_data['type'] in all_types:
        default_type_index = all_types.index(lucky_data['type'])
        default_store_val = lucky_data['name']
        is_lucky_mode = True
    else:
        # 如果轉到的類型不在選單裡，歸類到其他
        if "其他" in all_types:
            default_type_index = all_types.index("其他")
        default_store_val = lucky_data['name']
        is_lucky_mode = True

# --- 表單輸入區 ---
RESPONSES_CSV = "answers.csv"
ADMIN_PASSWORD = "900508"

date = st.date_input("📅 請選擇日期")
type_option = st.selectbox("🍱 餐廳類型", all_types, index=default_type_index)

selected_store = ""

# --- 核心邏輯：手動 vs 轉盤 ---

# 1. 如果是轉盤模式，且類型相符 -> 直接填入轉盤結果 (文字框)
if is_lucky_mode and type_option == st.session_state['lucky_result']['type']:
    st.success(f"📍 命運指定：{default_store_val}")
    selected_store = st.text_input("店家名稱", value=default_store_val)

# 2. 如果使用者手動選了有預設清單的類型 (如火鍋) -> 顯示手動下拉選單
elif type_option in STORE_MAP_MANUAL:
    store_list = STORE_MAP_MANUAL[type_option]
    chosen_store = st.selectbox(f"請選擇{type_option}店家", store_list)
    
    if chosen_store == "其他":
        selected_store = st.text_input(f"請輸入{type_option}店家名稱")
    else:
        selected_store = chosen_store

# 3. 如果選了其他 -> 顯示文字框
elif type_option == "其他":
    selected_store = st.text_input("請輸入餐廳名稱")

# 4. 如果選了 CSV 裡有但手動清單沒有的類型 -> 顯示文字框
else:
    selected_store = st.text_input(f"請輸入{type_option}店家名稱")

# --- 提交 ---
with st.form(key="response_form"):
    comment = st.text_area("💬 其他備註", height=80)
    submit_btn = st.form_submit_button("✅ 提交表單")

if submit_btn:
    if type_option == "請選擇": st.error("⚠️ 請選擇類型！")
    elif not selected_store: st.error("⚠️ 請輸入店名！")
    else:
        row = {"date": str(date), "type": type_option, "store": selected_store, "note": comment}
        df_row = pd.DataFrame([row])
        mode = "a" if os.path.exists(RESPONSES_CSV) else "w"
        header = not os.path.exists(RESPONSES_CSV)
        df_row.to_csv(RESPONSES_CSV, mode=mode, header=header, index=False, encoding="utf-8-sig")
        st.balloons(); st.success("提交成功！")

st.markdown("---")

# ==========================================
# ⚡ 極速轉盤 (使用 CSV 資料)
# ==========================================
st.header("⚡ 命運轉盤")
st.write("從你的口袋名單中隨機挑選！")

placeholder = st.empty()

if st.button("🚀 啟動命運引擎"):
    locs = list(active_db.keys())
    
    if not locs:
        st.error("資料庫為空，請確認 CSV 檔案是否正確！")
    else:
        # 動畫
        for i in range(10):
            t_loc = random.choice(locs)
            t_types = list(active_db[t_loc].keys())
            if not t_types: continue
            t_type = random.choice(t_types)
            t_store = random.choice(active_db[t_loc][t_type])
            
            placeholder.markdown(f"""
                <div class='big-font'>{t_loc} | {t_type}</div>
                <div class='small-addr'>{t_store['name']}</div>
            """, unsafe_allow_html=True)
            time.sleep(0.08)
        
        # 結果
        f_loc = random.choice(locs)
        f_types = list(active_db[f_loc].keys())
        if f_types:
            f_type = random.choice(f_types)
            f_store = random.choice(active_db[f_loc][f_type])
            
            placeholder.markdown(f"""
                <div style='text-align:center'>
                    <h3>✨ 鎖定：{f_store['name']}</h3>
                    <p>📍 {f_store['addr']}</p>
                    <p>📸 正在抓取照片...</p>
                </div>
                """, unsafe_allow_html=True)
            
            imgs = fetch_image_urls(f_store['name'], f_loc)
            
            st.session_state['lucky_result'] = {
                "name": f_store['name'],
                "addr": f_store['addr'],
                "type": f_type,
                "loc": f_loc,
                "imgs": imgs
            }
            st.rerun()
        else:
            st.error("選到的地區沒有餐廳資料！")

# 顯示轉盤結果
if st.session_state['lucky_result']:
    res = st.session_state['lucky_result']
    placeholder.empty()
    map_url = f"https://www.google.com/maps/search/?api=1&query={res['addr']}"
    
    st.markdown(f"""
    <div class="result-card">
        <h2>{res['name']}</h2>
        <div class="addr-text">📍 {res['addr']}</div>
        <p>類型：{res['type']} | 地區：{res['loc']}</p>
        <a href="{map_url}" target="_blank" class="map-link">🗺️ Google Maps 導航</a>
        <br><br>
        <p style="color:#ffffffaa; font-size:14px;">☝️ 表單已自動填好！</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: st.image(res['imgs'][0], use_container_width=True)
    with c2: st.image(res['imgs'][1], use_container_width=True)

# (管理者區保持不變)
password = st.text_input("🔒 管理者密碼", type="password")
if password == 900508:
    if os.path.exists(RESPONSES_CSV):
        df = pd.read_csv(RESPONSES_CSV, encoding="utf-8-sig")
        st.dataframe(df)
        st.download_button("📥 下載 CSV", open(RESPONSES_CSV, "rb"), "responses.csv")

