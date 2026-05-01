import pandas as pd
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- 設定區 ---
TARGET_URL = "https://vmo.17.media/2604-bingo/index.html?utm_campaign=24850&utm_content=tab-event-general&utm_medium=banner&utm_source=17live"
DATA_FILE = "bingo_history.csv"

def get_latest_numbers():
    """在 Linux 無頭環境下啟動瀏覽器並抓取號碼"""
    chrome_options = Options()
    
    # GitHub Actions 必須使用的參數
    chrome_options.add_argument("--headless")           # 不開啟視窗
    chrome_options.add_argument("--no-sandbox")          # 停用沙盒環境
    chrome_options.add_argument("--disable-dev-shm-usage") # 防止記憶體不足
    chrome_options.add_argument("--disable-gpu")         # 停用 GPU 加速
    chrome_options.add_argument("--window-size=1920,1080") # 設定視窗大小確保元件可見
    
    # 自動下載並安裝對應版本的 Chrome Driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print(f"正在前往網頁: {TARGET_URL}")
        driver.get(TARGET_URL)
        
        # 增加等待時間，確保 JavaScript 動態載入完成
        time.sleep(10) 
        
        # --- HTML 抓取邏輯 (這部分最容易隨網頁更新而改變) ---
        # 這裡假設開獎號碼所在的標籤具有特定 class，實際需依網頁檢查結果修改
        # 建議先手動檢查 17LIVE 網頁，看那 5 個數字的 CSS Class 是什麼
        elements = driver.find_elements(By.CLASS_NAME, "bingo-num") 
        
        # 如果 class 抓不到，也可以試著抓所有的 span 或 div 再過濾
        if not elements:
            print("警告：找不到指定 class 的元素，嘗試抓取所有數字...")
            # 備用方案範例：抓取特定父層下的所有文字
            # elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'number-row')]//span")
            
        numbers = []
        for e in elements:
            val = e.text.strip()
            if val.isdigit():
                numbers.append(int(val))
        
        if len(numbers) >= 5:
            # 只要前 5 個號碼
            return numbers[:5]
        else:
            print(f"錯誤：抓到的號碼數量不足 ({len(numbers)} 個)")
            return None
            
    except Exception as e:
        print(f"抓取過程中發生異常: {e}")
        return None
    finally:
        driver.quit()

def save_and_predict(new_nums):
    """更新 CSV 資料檔並輸出預測"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 讀取現有資料
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        # 如果檔案不存在，建立新表格
        df = pd.DataFrame(columns=["date", "n1", "n2", "n3", "n4", "n5"])
    
    # 檢查今日是否已存在
    if date_str in df['date'].values:
        print(f"今日 ({date_str}) 資料已存在，跳過儲存。")
    else:
        new_row = {
            "date": date_str, 
            "n1": new_nums[0], 
            "n2": new_nums[1], 
            "n3": new_nums[2], 
            "n4": new_nums[3], 
            "n5": new_nums[4]
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        # 存回 CSV
        df.to_csv(DATA_FILE, index=False)
        print(f"成功儲存號碼: {new_nums}")

    # --- 簡易預測邏輯 ---
    if len(df) > 0:
        # 1. 統計最常出現的熱門號
        all_nums = df[["n1", "n2", "n3", "n4", "n5"]].values.flatten()
        hot_numbers = pd.Series(all_nums).value_counts().head(5).index.tolist()
        
        # 2. 隨機推薦 (結合統計概念)
        # 這裡可以根據你的喜好增加複雜度
        print("\n==============================")
        print(f"📅 數據統計截止至: {date_str}")
        print(f"🔥 歷史最熱門號碼: {hot_numbers}")
        print(f"💡 建議明天嘗試: {hot_numbers}")
        print("==============================\n")

if __name__ == "__main__":
    print("啟動自動抓取任務...")
    result = get_latest_numbers()
    
    if result:
        save_and_predict(result)
    else:
        print("抓取失敗，請確認網頁結構是否改變或增加防爬機制。")