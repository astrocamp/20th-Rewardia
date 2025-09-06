from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# 設定 Chrome 選項
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # 無頭模式
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")

try:
    print("啟動 Chrome 瀏覽器...")
    driver = webdriver.Chrome(options=options)
    
    print("訪問袋鼠金融網站...")
    driver.get("https://roo.cash/creditcard/")
    
    print(f"頁面標題: {driver.title}")
    print(f"當前URL: {driver.current_url}")
    
    # 檢查是否能找到主要元素
    try:
        categories = driver.find_elements(By.CSS_SELECTOR, "a[type='button'][rel='opener']")
        print(f"找到 {len(categories)} 個分類連結")
        
        for i, cat in enumerate(categories[:3]):  # 只顯示前3個
            print(f"  {i+1}. {cat.get_attribute('href')}")
            
    except Exception as e:
        print(f"找不到分類元素: {e}")
    
    # 檢查頁面內容
    body_text = driver.find_element(By.TAG_NAME, "body").text[:200]
    print(f"頁面內容片段: {body_text}...")
    
    print("測試成功！")
    
except Exception as e:
    print(f"測試失敗: {e}")
    
finally:
    try:
        driver.quit()
        print("瀏覽器已關閉")
    except:
        pass