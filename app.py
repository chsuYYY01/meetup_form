import streamlit as st
import pandas as pd
import os
import random
import time
from duckduckgo_search import DDGS

# ---------- 網頁設定 ----------
st.set_page_config(
    page_title="聚餐大輪盤 (暗黑美化版)",
    page_icon="🍲",
    layout="centered"
)

# ---------- CSS 美化 (專為 Dark Mode 優化) ----------
st.markdown("""
    <style>
    /* 全局按鈕樣式 */
    .stButton>button {
        width: 100%;
        font-size: 20px;
        font-weight: bold;
        border-radius: 12px;
        background: linear-gradient(45deg, #FF4B4B, #FF914D); /* 漸層紅 */
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 75, 75, 0.6);
    }
    
    /* 轉盤跳動的大字體 */
    .big-font {
        font-size: 28px !important;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
        text-shadow: 0px 0px 10px rgba(255, 75, 75, 0.3);
    }
    
    /* 結果顯示卡片 (Dark Mode 適配) */
    .result-card {
        padding: 25px;
        border-radius: 16px;
        background-color: rgba(255, 255, 255, 0.05); /* 半透明玻璃感 */
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        margin-top: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        color: #ffffff; /* 強制白字 */
    }
    .result-card h3 {
        color: #FF4B4B !important;
        margin-bottom: 10px;
    }
    .result-card p {
        color: #e0e0e0 !important;
        font-size: 16px;
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
        image_urls.append("https://via.placeholder.com/400x300/333333/FFFFFF?text=Searching...")
    return image_urls

# ---------- 資料庫 1：命運轉盤 (真實人氣店) ----------
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

# ---------- 資料庫 2：手動下拉清單 ----------
STORE_MAP_MANUAL = {
    "火鍋": ["涮乃葉", "築間", "這一小鍋", "天香", "其他"],
    "韓式": ["涓豆腐", "永和樓", "韓華園", "香港飯店", "其他"],
    "義式": ["貳樓", "莫凡比", "亞丁尼", "其他"],
    "美式": ["Everywhere burger club", "JK Studio", "其他"],
    "日式": ["藏壽司", "一蘭拉麵", "彌生軒", "其他"],
    "燒肉": ["原燒", "乾杯", "其他"] # 補上燒肉的手動選項
}

# ---------- 初始化 Session State ----------
if 'lucky_result' not in st.session_state:
    st.session_state['lucky_result'] = None

# ==========================================
# 📝 第一部分：表單區 (智慧填入邏輯)
# ==========================================
st.title("🍽️ 聚餐表單")
st.info("⬇️ 點擊最下方的「極速轉盤」，系統會自動幫你填好表單！")

# --- 1. 計算預設值 ---
# 定義所有可能的類型 (加上燒肉)
type_options_list = ["請選擇", "火鍋", "韓式", "義式", "美式", "日式", "燒肉", "其他"]

default_type_index = 0 
default_store_val = ""
is_lucky_mode = False

if st.session_state['lucky_result']:
    lucky_data = st.session_state['lucky_result']
    lucky_type = lucky_data['type']
    
    # 檢查轉到的類型是否在我們的清單中
    if lucky_type in type_options_list:
        default_type_index = type_options_list.index(lucky_type)
        default_store_val = lucky_data['name']
        is_lucky_mode = True
    else:
        # 如果轉到的類型很特別 (防呆)，就歸類到其他
        default_type_index = type_options_list.index("其他")
        default_store_val = lucky_data['name']
        is_lucky_mode = True

# --- 表單開始 ---
RESPONSES_CSV = "answers.csv"
ADMIN_PASSWORD = "900508"

date = st.date_input("📅 請選擇日期")

# 這裡使用 index 來自動選定轉盤的類型 (例如：自動選成 "火鍋")
type_option = st.selectbox("🍱 餐廳類型", type_options_list, index=default_type_index)

selected_store = ""

# --- 2. 智慧輸入框邏輯 ---
# 邏輯：如果是轉盤模式，且使用者沒有切換類型，就直接顯示文字框並填入店名
# 這樣就不用管下拉選單裡有沒有這家店了，最直觀
if is_lucky_mode and type_option == st.session_state['lucky_result']['type']:
    st.success(f"⚡ 轉盤推薦：{default_store_val} ({st.session_state['lucky_result']['loc']})")
    selected_store = st.text_input("店家名稱", value=default_store_val)

# 如果使用者手動切換了類型 (例如原本轉到火鍋，但他改成韓式)，則回到一般下拉選單
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
# ⚡ 第二部分：極速轉盤 (Glassmorphism UI)
# ==========================================
st.header("⚡ 極速命運轉盤")
st.write("點擊下方按鈕，秒選台北/南崁美食。")

placeholder = st.empty()

if st.button("🚀 啟動命運引擎"):
    # 1. 動畫 (改用新的 CSS 樣式)
    locs = list(REAL_DB.keys())
    for i in range(10):
        temp_loc = random.choice(locs)
        temp_types = list(REAL_DB[temp_loc].keys())
        temp_type = random.choice(temp_types)
        temp_store = random.choice(REAL_DB[temp_loc][temp_type])
        
        # 這裡用 HTML 渲染金色漸層字體
        placeholder.markdown(f"<div class='big-font'>📍 {temp_loc} | {temp_type}<br>{temp_store}</div>", unsafe_allow_html=True)
        time.sleep(0.08)
    
    # 2. 決定結果
    final_loc = random.choice(locs)
    final_type = random.choice(list(REAL_DB[final_loc].keys()))
    final_store = random.choice(REAL_DB[final_loc][final_type])
    
    placeholder.markdown(f"""
        <div style='text-align:center'>
            <h3>✨ 鎖定目標：{final_loc} 的 <span style='color:#FF4B4B'>{final_store}</span></h3>
            <p>📸 正在從雲端下載美食照...</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 3. 抓圖
    imgs = fetch_image_urls(final_store, final_loc)
    
    # 4. 存檔並刷新 (這會觸發上方的自動填入)
    st.session_state['lucky_result'] = {
        "name": final_store,
        "type": final_type,
        "loc": final_loc,
        "imgs": imgs
    }
    st.rerun()

# --- 顯示結果卡片 (使用新的 Dark Mode CSS) ---
if st.session_state['lucky_result']:
    res = st.session_state['lucky_result']
    placeholder.empty()
    
    st.markdown(f"""
    <div class="result-card">
        <h3>🎉 命運指定：{res['name']}</h3>
        <p>📍 地點：{res['loc']} | 類型：{res['type']}</p>
        <p style="color:#FF914D !important; font-weight:bold;">☝️ 表單已自動切換為「{res['type']}」並填入店名！</p>
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
