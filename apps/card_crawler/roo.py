from selenium import webdriver
from selenium.webdriver.common.by import By
import random
from selenium.common.exceptions import WebDriverException, ElementNotVisibleException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.relative_locator import locate_with
import time

driver = webdriver.Chrome()

main_url_page = "https://roo.cash/creditcard/"
sleep_time = (random.randint(7,14))/10

try:
    driver.get(main_url_page)
    driver.implicitly_wait(2)
except WebDriverException as error:
    print(f"Error fetching main page: {error}")


try:
    card_names = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='product-detail']")
    card_urls = [card.get_attribute('href') for card in card_names]
except ElementNotVisibleException as error:
    print(f"Error fetching element: {error}")
    driver.quit()

def get_card_info(url):
    print(f"Processing: {url}")
    driver.get(url)

    content_arr = []

    try:
        # 找到卡的名字
        card_name = driver.find_element(By.CSS_SELECTOR,'h1[data-testid="product-title"]')
        # 把卡片加到content_arr裡，卡片名是串列裡的第一個元素
        # strip 會刪除前後的空格
        # 把card和url存成字典，存成串列的第一個元素，方便查找資料
        content_arr.append({
            "card":f"{card_name.text.strip()}",
            "url":f"{url}"
        })
    except WebDriverException as error:
        # 找不到卡的新增一個找不到的資訊
        content_arr.append("Card name not found")
        print(f"Error fetching card: {error}")


    try:
        # 找到navbar和footer之間的所有button
        buttons = driver.find_elements(locate_with(By.TAG_NAME, "button").below({By.TAG_NAME: "nav"}).above({By.TAG_NAME:"footer"}))
        action = ActionChains(driver)

        # 點選這些button，讓他們展開，因為資訊隱藏在裡面
        for button in buttons:
            action.click(on_element=button)

        # perform會執行click的動作
        action.perform()
        # 休息1秒讓資訊有時間顯示
        time.sleep(1)
    except WebDriverException as error:
        print(f"Error fetching button: {error}")

    # 找到navbar和footer之間的所有h4, h5, li, p的元素
    try:
        contents = driver.find_elements(locate_with(By.CSS_SELECTOR,"h4,h5,li,p").above({By.XPATH:"//h2[text()='其他推薦信用卡']"}).below({By.TAG_NAME: "nav"}))
        # 把它存到array
        for content in contents:
            # 排出空白的
            if len(content.text)>1:
                content_arr.append(content.text)
        print(f"Processing {card_name.text} finished")
    except WebDriverException as error:
        print(f"Error finding content: {error}")
    
    return content_arr


failed_cards = []
all_cards_data = []

for i, card_url in enumerate(card_urls):
    try:
        # 找尋每張卡頁面的資料
        card_data = get_card_info(card_url)
        # 將資料存到這個串列
        all_cards_data.append(card_data)
        print(card_data)
        time.sleep(sleep_time)
  
    except WebDriverException as error:
        failed_cards.append(card_url)
        print(f"Error fetching page {card_url}: {error}")


print(f"Successfully processed: {len(all_cards_data)} cards")
print(f"Failed: {len(failed_cards)} cards")

driver.quit()