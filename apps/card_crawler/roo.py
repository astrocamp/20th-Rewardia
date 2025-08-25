from selenium import webdriver
from selenium.webdriver.common.by import By
import random
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.relative_locator import locate_with
from urllib.parse import urlparse
import time

# 把整個爬蟲包成一個function
def crawl_roo_cards():
    driver = webdriver.Chrome()

    try:
        main_url_page = "https://roo.cash/creditcard/"
        sleep_time = random.uniform(7,14)

        try:
            driver.get(main_url_page)
            # 在尋找物件前要等多久
            driver.implicitly_wait(2)
        except WebDriverException as error:
            print(f"Error fetching main page: {error}")
            driver.quit()


        try:
            card_names = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='product-detail']")
            card_urls = [card.get_attribute('href') for card in card_names]
        except WebDriverException as error:
            print(f"Error fetching element: {error}")

        def get_card_info(url):

            try:
                print(f"Processing: {url}")
                driver.get(url)

                try:
                    # 找到卡的名字
                    card_name = driver.find_element(By.CSS_SELECTOR,'h1[data-testid="product-title"]')
                    # 把卡片加到content_arr裡，卡片名是串列裡的第一個元素
                    # strip 會刪除前後的空格
                    # 把card和url存成字典，存成串列的第一個元素，方便查找資料
                    
                except WebDriverException as error:
                    # 找不到卡，就回傳這個字典
                    error_data = {
                        "card":"Card not found.",
                        "url":f"{url}",
                        "error":f"{error}"
                    }
                    print(f"Error fetching card: {error}")
                    return error_data


                try:
                    # 找到navbar和footer之間的所有button
                    buttons = driver.find_elements(locate_with(By.TAG_NAME, "button").below({By.TAG_NAME: "nav"}).above({By.TAG_NAME:"footer"}))
                    action = ActionChains(driver)

                    # 點選這些button，讓他們展開，因為資訊隱藏在裡面
                    for button in buttons:
                        driver.execute_script("arguments[0].scrollIntoView(true);",button)
                        action.move_to_element(button).click(on_element=button)

                    # perform會執行click的動作
                    action.perform()
                    try:
                        # 比較節省時間的等待方式，如果元素在5秒內還沒出現就會回傳錯誤
                        WebDriverWait(driver,5).until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "answer")))
                    except TimeoutException:
                        print("Error fetching elements")
                except WebDriverException as error:
                    print(f"Error fetching button: {error}")

                # 找到navbar和footer之間的所有h4, h5, li, p的元素
                try:
                    # 將抓取到的資料整理成字典
                    crawled_data={
                        "card":f"{card_name.text.strip()}",
                        "url":f"{url}",
                        "url_domain":f"{urlparse(url).netloc}",
                        "content":[]
                    }

                    contents = driver.find_elements(locate_with(By.CSS_SELECTOR,"h4,h5,li,p").above({By.XPATH:"//h2[text()='其他推薦信用卡']"}).below({By.TAG_NAME: "nav"}))
                    # 把它存到array
                    for content in contents:
                        # 排出空白的
                        if len(content.text)>1:
                            crawled_data["content"].append(content.text)

                    # 成功的話，才會回傳值
                    return crawled_data
                except WebDriverException as error:
                    print(f"Error finding content: {error}")

            except WebDriverException as error:
                print(f"Card not found: {error}")
                # 找不到卡，就終止這次的函式
                return error

        failed_cards = []

        for i, card_url in enumerate(card_urls):
            try:
                # 找尋每張卡頁面的資料
                card_data = get_card_info(card_url)
                # 將資料存到這個串列
                print(card_data)
                time.sleep(sleep_time)
        
            except WebDriverException as error:
                failed_cards.append(card_url)
                print(f"Error fetching page {card_url}: {error}")


        # print(f"Successfully processed: {len(all_cards_data)} cards")
        print(f"Failed: {len(failed_cards)} cards")


    finally:
        # 關閉查找
        print("Closing webdriver.")
        driver.quit()

# 把整個爬蟲包成一個function
# 加這個讓它需要時可以方便import整個function到其他檔案
if __name__ == "__main__":
    crawl_roo_cards()