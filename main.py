import pandas as pd
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 設定區 ---
TARGET_URL = "https://vmo.17.media/2604-bingo/index.html?utm_campaign=24850&utm_content=tab-event-general&utm_medium=banner&utm_source=17live"
DATA_FILE = "bingo_history.csv"

def get_latest_numbers():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print(f"正在前往網頁: {TARGET_URL}")
        driver.get(TARGET_URL)
        
        # 增加強制等待時間，確保所有動態內容載入
        time.sleep(15) 

        # --- 策略：抓取網頁中所有「純數字」標籤 ---
        # 我們不再依賴那個 sc-xxxx 的 Class，改用標籤過濾
        all_tags = driver.find_elements(By.XPATH, "//div | //span | //p")
        
        raw_numbers = []
        for tag in all_tags:
            try:
                val = tag.text.strip()
                # 判斷是否為 1-99 的數字，且長度通常是 1-2 位數
                if val.isdigit() and 1 <= int(val) <= 99:
                    raw_numbers.append(int(val))
            except:
                continue

        # 過濾重複數字並保持出現順序
        unique_nums = []
        for n in raw_numbers:
            if n not in unique_nums:
                unique_nums.append(n)

        print(f"掃描到的所有疑似號碼: {unique_nums}")

        # 17LIVE 賓果通常每天開 5 個號碼
        # 如果抓到很多數字，根據網頁排版，開獎號碼通常會是連續出現的一組
        # 這裡我們取「最後出現」的 5 個數字（通常是開獎區）
        if len(unique_nums) >= 5:
            # 你可以根據 Log 輸出的順序調整取前 5 個 [:5] 或後 5 個 [-5:]
            final_nums = unique_nums[:5] 
            return final_nums
        else:
            print(f"失敗：僅掃描到 {len(unique_nums)} 個數字，不足 5 個。")
            return None
            
    except Exception as e:
        print(f"抓取過程中發生異常: {e}")
        return None
    finally:
        driver.quit()

def save_and_predict(new_nums):
    """更新 CSV 資料檔並輸出預測"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=["date", "n1", "n2", "n3", "n4", "n5"])
    
    if date_str in df['date'].values:
        print(f"今日 ({date_str}) 資料已存在，跳過。")
    else:
        new_row = {"date": date_str, "n1": new_nums[0], "n2": new_nums[1], "n3": new_nums[2], "n4": new_nums[3], "n5": new_nums[4]}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        print(f"成功更新資料庫：{new_nums}")

    # --- 預測邏輯 ---
    if not df.empty:
        all_history = df[["n1", "n2", "n3", "n4", "n5"]].values.flatten()
        hot_5 = pd.Series(all_history).value_counts().head(5).index.tolist()
        print("\n" + "="*30)
        print(f"📊 歷史開獎次數最多號碼: {hot_5}")
        print(f"🔮 明日預測參考: {hot_5}")
        print("="*30 + "\n")

if __name__ == "__main__":
    result = get_latest_numbers()
    if result:
        save_and_predict(result)
