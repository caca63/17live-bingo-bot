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
    """在 Linux 無頭環境下啟動瀏覽器並精準抓取號碼"""
    chrome_options = Options()
    
    # GitHub Actions 必須使用的參數
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # 偽裝瀏覽器指紋
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print(f"正在前往網頁: {TARGET_URL}")
        driver.get(TARGET_URL)
        
        # 使用顯式等待：等待該數字元件出現在畫面上，最長等 20 秒
        wait = WebDriverWait(driver, 20)
        # 注意：CSS Selector 中，空格要換成點，所以 sc-1d51a4b1-8 ihNWIJ 變成 .sc-1d51a4b1-8.ihNWIJ
        target_css = ".sc-1d51a4b1-8.ihNWIJ"
        
        print("等待元件載入...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, target_css)))
        
        # 額外停留一下確保數字內容填入
        time.sleep(5)
        
        # 抓取所有符合該 Class 的元素
        elements = driver.find_elements(By.CSS_SELECTOR, target_css)
        
        numbers = []
        for e in elements:
            val = e.text.strip()
            if val.isdigit():
                numbers.append(int(val))
        
        print(f"原始抓取結果: {numbers}")

        # 如果抓到的號碼很多（例如包含歷史紀錄），我們通常取最新的 5 個
        # 17LIVE 這種頁面通常前 5 個就是當天最新的
        if len(numbers) >= 5:
            final_nums = numbers[:5]
            return final_nums
        else:
            print(f"錯誤：僅抓到 {len(numbers)} 個數字，不足 5 個。")
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
