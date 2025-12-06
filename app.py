import streamlit as st
import pandas as pd
import os
import random
import time
from duckduckgo_search import DDGS

# ---------- 網頁設定 ----------
st.set_page_config(
    page_title="聚餐大輪盤",
    page_icon="🎰",
    layout="centered"
)

# ---------- CSS 美化 (讓按鈕跟標題更好看) ----------
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
        font-size: 30px !important;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
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

# ---------- 自動爬蟲函式 (含快取) ----------
@st.cache_data(ttl=3600)
def fetch_image_urls(query_text, max_imgs=2):
    image_urls = []
    try:
        search_query = f"{query_text} 美食"
        with DDGS() as ddgs:
            results = list(ddgs.images(search_query, max_results=max_imgs))
            for res in results:
                image_urls.append(res['image'])
    except Exception:
        return ["https://via.placeholder.com/400x300?text=No+Image"] * max_imgs
    
    if not image_urls:
        return ["https://via.placeholder.com/400x300?text=Not+Found"] * max_imgs
    return image_urls

# ---------- 資料庫 ----------
RESTAURANT_DB = {
    "火鍋": ["涮乃葉", "築間幸福鍋物", "這一小鍋", "天香回味"],
    "韓式": ["韓華園", "涓豆腐", "豚花", "永和樓"],
    "義式": ["Solo Pasta", "貳樓 Second Floor", "莫凡比", "亞丁尼義式麵屋"],
    "美式": ["Everywhere burger club", "JK Studio", "GB鮮釀餐廳"],
    "日式": ["藏壽司", "一蘭拉麵", "彌生軒", "大戶屋"]
}

# ---------- 初始化 Session State ----------
if 'lucky_result' not in st.session_state:
    st.session_state['lucky_result'] = None # 存整個結果物件

# ==========================================
# 📝 第一部分：正規表單 (移到最上面)
# ==========================================
st.title("🍽️ 聚餐表單")
st.info("請先填寫表單。如果不知道吃什麼，請滑到最下面玩命運轉盤！⬇️")

# --- 讀取轉盤結果 (如果有的話) ---
default_type_index = 0
default_store_val = ""
# 檢查是否剛轉完，且要帶入
if st.session_state['lucky_result']:
    res = st.session_state['lucky_result']
    # 嘗試自動對應類型
    all_types = ["請選擇", "火鍋", "韓式", "義式", "美式", "日式", "其他"]
    if res['type'] in all_types:
        default_type_index = all_types.index(res['type'])
        default_store_val = res['name']

# --- 表單開始 ---
RESPONSES_CSV = "answers.csv"
ADMIN_PASSWORD = "900508"

date = st.date_input("📅 請選擇日期")

# 這裡稍微修改邏輯，讓它可以吃轉盤的預設值
type_options = ["請選擇", "火鍋", "韓式", "義式", "美式", "日式", "其他"]
type_option = st.selectbox("🍱 餐廳類型", type_options, index=default_type_index)

# 根據類型顯示店家 (這裡簡化處理，讓轉盤結果可以直接填入)
selected_store = ""
store_map = {
    "火鍋": ["涮乃葉", "築間", "這一小鍋", "天香", "其他"],
    "韓式": ["涓豆腐", "永和樓", "韓華園", "香港飯店", "其他"],
    "義式": ["貳樓", "莫凡比", "亞丁尼", "其他"],
    "美式": ["Everywhere burger club", "JK Studio", "其他"],
    "日式": ["藏壽司", "一蘭拉麵", "彌生軒", "其他"]
}

# 邏輯：如果是轉盤轉出來的，且使用者沒改類型，優先顯示轉盤店名
if type_option != "請選擇":
    # 先看是不是轉盤推薦的
    if default_store_val and type_option == st.session_state['lucky_result']['type']:
        st.success(f"💡 已自動填入轉盤推薦：{default_store_val}")
        selected_store = st.text_input("店家名稱", value=default_store_val)
    else:
        # 一般手動選擇
        if type_option in store_map:
            s_list = store_map[type_option]
            s_opt = st.selectbox(f"請選擇{type_option}店家", s_list)
            selected_store = st.text_input(f"請輸入{type_option}名稱") if s_opt == "其他" else s_opt
        else:
            selected_store = st.text_input("請輸入餐廳名稱")

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
# 🎰 第二部分：命運轉盤 (移到下面 + 酷炫動畫)
# ==========================================
st.header("🎲 命運轉盤區")
st.write("不知道吃什麼？按下按鈕，讓命運決定！")

# 這裡使用一個空的容器來做動畫效果
placeholder = st.empty()

# 啟動按鈕
if st.button("🚀 啟動超級轉盤 (包含搜圖)"):
    
    # 1. 老虎機抽獎動畫 (Shuffle Effect)
    # 我們隨機顯示幾個選項，製造快速跳動的感覺
    all_types = list(RESTAURANT_DB.keys())
    
    # 動畫迴圈
    for i in range(15): # 跳動 15 次
        temp_type = random.choice(all_types)
        temp_store = random.choice(RESTAURANT_DB[temp_type])
        
        # 使用 HTML 讓字體變大變色，製造閃爍感
        placeholder.markdown(
            f"<div class='big-font'>🎲 {temp_type} | {temp_store}...</div>", 
            unsafe_allow_html=True
        )
        time.sleep(0.1) # 每次停留 0.1 秒
    
    # 2. 決定最終結果
    final_type = random.choice(all_types)
    final_store = random.choice(RESTAURANT_DB[final_type])
    
    # 3. 顯示搜尋中動畫 (這就是你要的 2-3 秒查找畫面)
    placeholder.markdown(
        f"""
        <div style='text-align:center'>
            <h3>✨ 命運已選定：<span style='color:#FF4B4B'>{final_store}</span></h3>
            <p>🕵️‍♂️ 正在前往 Google/IG 挖掘這家店的美食照...</p>
            <p>(請稍等 2~3 秒)</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # 這裡真的去搜尋 (會花一點時間，剛好配合上面的文字)
    imgs = fetch_image_urls(final_store)
    time.sleep(1) # 額外加一點延遲，讓使用者看清楚「正在搜尋」的字樣，更有儀式感

    # 4. 存入 Session State (讓頁面重整後還在)
    st.session_state['lucky_result'] = {
        "type": final_type,
        "name": final_store,
        "imgs": imgs
    }
    
    # 強制重新執行一次腳本，讓上方的表單可以抓到新的 session_state 值並自動填入
    st.rerun()

# --- 顯示轉盤結果 (如果有) ---
if st.session_state['lucky_result']:
    res = st.session_state['lucky_result']
    
    # 清空 placeholder，改顯示正式結果卡片
    placeholder.empty() 
    
    st.markdown(f"""
    <div class="result-card">
        <h2>🎉 推薦結果：{res['type']}</h2>
        <h1>{res['name']}</h1>
        <p>☝️ 上面的表單已經自動幫你填好這家店囉！</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.image(res['imgs'][0], use_container_width=True, caption="熱門照片 1")
    with col2:
        st.image(res['imgs'][1], use_container_width=True, caption="熱門照片 2")

st.markdown("---")

# ---------- 管理者模式 ----------
password = st.text_input("🔒 管理者密碼", type="password")
if password == ADMIN_PASSWORD:
    if os.path.exists(RESPONSES_CSV):
        df = pd.read_csv(RESPONSES_CSV, encoding="utf-8-sig")
        st.dataframe(df)
        st.download_button("📥 下載 CSV", open(RESPONSES_CSV, "rb"), "responses.csv")
