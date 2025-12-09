import streamlit as st
import pandas as pd
import os
import random
import time
import streamlit.components.v1 as components # 👈 引入這個元件來跑 HTML/JS
from duckduckgo_search import DDGS

# ---------- 網頁設定 ----------
st.set_page_config(
    page_title="聚餐大輪盤 (真實動畫版)",
    page_icon="🎡",
    layout="centered"
)

# ---------- CSS 美化 ----------
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

# ---------- 核心功能：HTML5 Canvas 轉盤 (JavaScript) ----------
def wheel_animation(items, winner_index):
    """
    這段程式碼會生成一個 HTML/JS 轉盤。
    Python 會先決定 winner_index，然後 JS 負責演戲轉到那個位置。
    """
    # 轉成 JS 陣列字串
    items_js = str(items).replace("'", '"') 
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; background: transparent; overflow: hidden; }}
        .wheel-container {{ position: relative; width: 300px; height: 300px; }}
        canvas {{ width: 100%; height: 100%; transform: rotate(-90deg); }}
        .arrow {{
            position: absolute;
            top: 50%;
            right: -20px;
            transform: translateY(-50%);
            width: 0; 
            height: 0; 
            border-top: 15px solid transparent;
            border-bottom: 15px solid transparent;
            border-right: 30px solid #FF4B4B; /* 指針顏色 */
        }}
    </style>
    </head>
    <body>
        <div class="wheel-container">
            <canvas id="wheel" width="500" height="500"></canvas>
            <div class="arrow"></div>
        </div>

        <script>
            const canvas = document.getElementById('wheel');
            const ctx = canvas.getContext('2d');
            const items = {items_js};
            const winnerIdx = {winner_index}; // Python 傳進來的贏家索引
            
            const colors = ['#FF9AA2', '#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA', '#f8d5f6', '#ebd4aa'];
            const n = items.length;
            const arc = 2 * Math.PI / n;
            let startAngle = 0;
            let spinTimeout = null;
            
            // 畫轉盤
            function drawWheel() {{
                for (let i = 0; i < n; i++) {{
                    const angle = startAngle + i * arc;
                    ctx.beginPath();
                    ctx.fillStyle = colors[i % colors.length];
                    ctx.moveTo(250, 250);
                    ctx.arc(250, 250, 250, angle, angle + arc);
                    ctx.lineTo(250, 250);
                    ctx.fill();
                    
                    // 文字
                    ctx.save();
                    ctx.translate(250 + Math.cos(angle + arc / 2) * 180, 250 + Math.sin(angle + arc / 2) * 180);
                    ctx.rotate(angle + arc / 2 + Math.PI); // 文字轉向
                    ctx.fillStyle = "#333";
                    ctx.font = "bold 24px Arial";
                    const text = items[i].length > 8 ? items[i].substring(0,7)+"..." : items[i];
                    ctx.fillText(text, -ctx.measureText(text).width / 2, 5);
                    ctx.restore();
                }}
            }}

            // 動畫邏輯
            let currentAngle = 0;
            // 計算目標角度：我們要讓指針(0度/360度)指向贏家
            // 因為 Canvas 旋轉了 -90度，且指針在右邊(0度)，
            // 我們需要反向計算。這是一個 hack，確保最後停在 Python 指定的位置。
            // 贏家位置的中心角度 = winnerIdx * arc + arc/2
            // 我們要旋轉轉盤，使得這個角度對齊 0 度。
            // 加上 10 圈 (10 * 2PI) 製造旋轉感
            
            // 經過精密計算的作弊角度
            const rotateAngle = (10 * 2 * Math.PI) - ((winnerIdx * arc) + (arc/2));
            
            let spinTime = 0;
            const spinTimeTotal = 4000; // 轉 4 秒
            
            function rotate() {{
                spinTime += 20;
                if(spinTime >= spinTimeTotal) {{
                    drawWheel();
                    return;
                }}
                
                // 緩動函數 (Ease Out)
                const p = spinTime / spinTimeTotal;
                const delta = (1 - Math.pow(1 - p, 3)) * rotateAngle; // Cubic Ease Out
                
                startAngle = delta;
                ctx.clearRect(0, 0, 500, 500);
                drawWheel();
                requestAnimationFrame(rotate);
            }}

            drawWheel();
            setTimeout(rotate, 100); // 啟動旋轉
        </script>
    </body>
    </html>
    """
    # 渲染 HTML，高度設為 320px
    components.html(html_code, height=320)

# ---------- 爬圖函式 ----------
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

# ---------- CSV 讀取 ----------
def load_db_from_csv(csv_path_or_file):
    try:
        df = pd.read_csv(csv_path_or_file)
        required = {'地區', '類型', '店名', '地址'}
        if not required.issubset(df.columns):
            return None, "CSV 缺少必要欄位"
        
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

# ---------- 預設資料 ----------
STORE_MAP_MANUAL = {
    "火鍋": ["涮乃葉", "築間", "這一小鍋", "天香", "其他"],
    "韓式": ["涓豆腐", "永和樓", "韓華園", "香港飯店", "其他"],
    "義式": ["貳樓", "莫凡比", "亞丁尼", "其他"],
    "美式": ["Everywhere burger club", "JK Studio", "其他"],
    "日式": ["藏壽司", "一蘭拉麵", "彌生軒", "其他"],
    "燒肉": ["原燒", "乾杯", "其他"]
}

DEFAULT_BACKUP_DB = {
    "台北": {"火鍋": [{"name": "詹記麻辣火鍋", "addr": "台北市大安區"}]},
    "南崁": {"火鍋": [{"name": "築間幸福鍋物", "addr": "桃園市蘆竹區"}]}
}

# ---------- Init Session ----------
if 'lucky_result' not in st.session_state:
    st.session_state['lucky_result'] = None
# 新增一個狀態來控制動畫顯示
if 'show_wheel' not in st.session_state:
    st.session_state['show_wheel'] = False

# ==========================================
# 📂 資料來源
# ==========================================
st.sidebar.header("📂 資料來源")
uploaded_file = st.sidebar.file_uploader("上傳清單 (CSV)", type=["csv"])
LOCAL_CSV = "my_restaurants.csv"
active_db = {}
source_msg = ""

if uploaded_file:
    db, err = load_db_from_csv(uploaded_file)
    active_db = db if db else DEFAULT_BACKUP_DB
    source_msg = "目前使用：**使用者上傳清單**"
elif os.path.exists(LOCAL_CSV):
    db, err = load_db_from_csv(LOCAL_CSV)
    active_db = db if db else DEFAULT_BACKUP_DB
    source_msg = "目前使用：**我的口袋名單**"
else:
    active_db = DEFAULT_BACKUP_DB
    source_msg = "目前使用：**系統備用範例**"

st.session_state['active_db'] = active_db

# ==========================================
# 📝 主畫面
# ==========================================
st.title("🍽️ 聚餐表單")
st.caption(f"🎯 {source_msg}")

# 下拉選單處理
current_db_types = set()
for loc in st.session_state['active_db']:
    current_db_types.update(st.session_state['active_db'][loc].keys())

manual_types = set(STORE_MAP_MANUAL.keys())
all_types = sorted(list(manual_types | current_db_types), key=lambda x: (x=="其他", x=="請選擇", x))
if "請選擇" not in all_types: all_types.insert(0, "請選擇")
if "其他" in all_types: all_types.remove("其他"); all_types.append("其他")

# 預設值
default_type_index = 0 
default_store_val = ""
is_lucky_mode = False

if st.session_state['lucky_result']:
    lucky_data = st.session_state['lucky_result']
    if lucky_data['type'] in all_types:
        default_type_index = all_types.index(lucky_data['type'])
        default_store_val = lucky_data['name']
        is_lucky_mode = True
    else:
        if "其他" in all_types: default_type_index = all_types.index("其他")
        default_store_val = lucky_data['name']
        is_lucky_mode = True

# 表單輸入
RESPONSES_CSV = "answers.csv"
ADMIN_PASSWORD = "900508"

date = st.date_input("📅 請選擇日期")
type_option = st.selectbox("🍱 餐廳類型", all_types, index=default_type_index)
selected_store = ""

if is_lucky_mode and type_option == st.session_state['lucky_result']['type']:
    st.success(f"📍 命運指定：{default_store_val}")
    selected_store = st.text_input("店家名稱", value=default_store_val)
elif type_option in STORE_MAP_MANUAL:
    store_list = STORE_MAP_MANUAL[type_option]
    chosen_store = st.selectbox(f"請選擇{type_option}店家", store_list)
    selected_store = st.text_input(f"請輸入{type_option}店家名稱") if chosen_store == "其他" else chosen_store
elif type_option == "其他":
    selected_store = st.text_input("請輸入餐廳名稱")
else:
    selected_store = st.text_input(f"請輸入{type_option}店家名稱")

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
# 🎡 真・動畫轉盤
# ==========================================
st.header("🎡 命運轉盤")
st.write("點擊按鈕，召喚真實轉盤！")

# 這裡使用 container 來控制顯示區域
wheel_zone = st.container()

if st.button("🚀 啟動命運引擎"):
    locs = list(active_db.keys())
    
    if not locs:
        st.error("資料庫為空，請確認 CSV 檔案是否正確！")
    else:
        # 1. Python 先作弊算出結果
        f_loc = random.choice(locs)
        f_types = list(active_db[f_loc].keys())
        if f_types:
            f_type = random.choice(f_types)
            f_store = random.choice(active_db[f_loc][f_type])
            
            # 準備轉盤選項：為了不讓轉盤太擠，我們取同地區的一些餐廳混進去
            # 或者如果太少，就隨機塞一些 "再來一次"
            wheel_items = []
            # 嘗試抓取該地區該類型的所有餐廳當作選項
            candidates = [s['name'] for s in active_db[f_loc][f_type]]
            
            # 如果選項太少(<4)，我們補一些其他的
            if len(candidates) < 4:
                # 補該地區其他類型的
                for t in f_types:
                    candidates.extend([s['name'] for s in active_db[f_loc][t]])
            
            # 去重並取最多 8 個，確保贏家在裡面
            wheel_items = list(set(candidates))
            if f_store['name'] not in wheel_items:
                wheel_items.append(f_store['name'])
            
            random.shuffle(wheel_items)
            wheel_items = wheel_items[:8] # 最多8個切片
            
            # 確保贏家在裡面 (以防 shuffle 切掉)
            if f_store['name'] not in wheel_items:
                wheel_items[0] = f_store['name']
            
            # 找到贏家的 index
            winner_idx = wheel_items.index(f_store['name'])
            
            # 2. 顯示轉盤動畫
            with wheel_zone:
                st.info(f"🎯 目標鎖定範圍：{f_loc} 的 {f_type}...")
                # 呼叫 JS 轉盤
                wheel_animation(wheel_items, winner_idx)
                
                # 為了配合動畫時間 (JS 設定轉 4 秒)，Python 這裡暫停一下
                # 這樣結果卡片才不會在轉盤還在轉的時候就劇透
                time.sleep(4.2)
            
            # 3. 抓圖並顯示結果
            imgs = fetch_image_urls(f_store['name'], f_loc)
            
            st.session_state['lucky_result'] = {
                "name": f_store['name'],
                "addr": f_store['addr'],
                "type": f_type,
                "loc": f_loc,
                "imgs": imgs
            }
            st.rerun() # 重新整理以顯示結果卡片
        else:
            st.error("選到的地區沒有餐廳資料！")

# 顯示轉盤結果
if st.session_state['lucky_result']:
    res = st.session_state['lucky_result']
    map_url = f"https://www.google.com/maps/search/?api=1&query={res['addr']}"
    
    st.markdown(f"""
    <div class="result-card">
        <h2>🎉 恭喜選中：{res['name']}</h2>
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

# 管理者區
st.markdown("---")
st.subheader("🔒 管理者專區")
password = st.text_input("請輸入管理密碼", type="password")
if password == ADMIN_PASSWORD:
    st.success("✅ 登入成功！")
    if os.path.exists(RESPONSES_CSV):
        df = pd.read_csv(RESPONSES_CSV, encoding="utf-8-sig")
        st.write(f"📊 共 {len(df)} 筆資料")
        st.dataframe(df)
        st.download_button("📥 下載 CSV", open(RESPONSES_CSV, "rb"), "responses.csv", "text/csv")
    else:
        st.warning("📭 目前尚無資料")
elif password:
    st.error("❌ 密碼錯誤")
