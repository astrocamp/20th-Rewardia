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
from apps.card_crawler.models import CrawledData
from apps.cards.models import CreditCard
from apps.banks.models import Bank


# 範例，把資料存到資料庫，還無法正式存，因為credit card db還沒見起來
# 這個函式到時候會放到command的資料夾裡
def save_data(data):
    # 先找銀行，如果銀行沒有在db，那就創建銀行
    bank, created = Bank.objects.get_or_create(
        name=data["bank"],
    )

    # 如果這張卡沒有在db，那就會在cards創建一張
    card, created = CreditCard.objects.get_or_create(
        name=data["card"],
        bank=bank,
    )

    # 用逗點把爬到的資料接起來
    content = ",".join(data["content"])
    # 這裡是存到爬到的資料的資料庫
    CrawledData.objects.create(
        card=card,
        url=data["url"],
        url_domain=data["url_domain"],
        content=content,
    )


# 把整個爬蟲包成一個function
def crawl_roo_cards():
    driver = webdriver.Chrome()

    try:
        main_url_page = "https://roo.cash/creditcard/"
        sleep_time = random.uniform(7, 14)

        try:
            driver.get(main_url_page)
            # 在尋找物件前要等多久
            driver.implicitly_wait(2)
        except WebDriverException as error:
            print(f"Error fetching main page: {error}")
            driver.quit()

        try:
            card_names = driver.find_elements(
                By.CSS_SELECTOR, "a[data-testid='product-detail']"
            )
            card_urls = [card.get_attribute("href") for card in card_names]
        except WebDriverException as error:
            print(f"Error fetching element: {error}")

        def get_card_info(url):
            try:
                print(f"Processing: {url}")
                driver.get(url)

                try:
                    # 找到卡的名字
                    card_name = driver.find_element(
                        By.CSS_SELECTOR, 'h1[data-testid="product-title"]'
                    ).text.strip()
                    # 發現銀行就在卡名裡：「中國信託 LINE Pay 信用卡」
                    bank_name = card_name.split(" ")[0]

                except WebDriverException as error:
                    # 找不到卡，就回傳這個字典
                    error_data = {
                        "card": "Card not found.",
                        "url": f"{url}",
                        "error": f"{error}",
                    }
                    print(f"Error fetching card: {error}")
                    return error_data

                try:
                    # 找到navbar和footer之間的所有button
                    buttons = driver.find_elements(
                        locate_with(By.TAG_NAME, "button")
                        .below({By.TAG_NAME: "nav"})
                        .above({By.TAG_NAME: "footer"})
                    )
                    action = ActionChains(driver)

                    # 點選這些button，讓他們展開，因為資訊隱藏在裡面
                    for button in buttons:
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});", button
                        )
                        action.move_to_element(button).click(on_element=button)

                    # perform會執行click的動作
                    action.perform()
                    try:
                        # 比較節省時間的等待方式，如果元素在5秒內還沒出現就會回傳錯誤
                        WebDriverWait(driver, 5).until(
                            EC.visibility_of_all_elements_located(
                                (By.CLASS_NAME, "answer")
                            )
                        )
                    except TimeoutException:
                        print("Error fetching elements")
                except WebDriverException as error:
                    print(f"Error fetching button: {error}")

                # 找到navbar和footer之間的所有h4, h5, li, p的元素
                try:
                    # 將抓取到的資料整理成字典
                    crawled_data = {
                        "card": card_name,
                        "bank": bank_name,
                        "url": url,
                        "url_domain": f"{urlparse(url).netloc}",
                        "content": [],
                    }

                    contents = driver.find_elements(
                        locate_with(By.CSS_SELECTOR, "h4,h5,li,p")
                        .above({By.XPATH: "//h2[text()='其他推薦信用卡']"})
                        .below({By.TAG_NAME: "nav"})
                    )
                    # 把它存到array
                    for content in contents:
                        # 排出空白的
                        if len(content.text) > 1:
                            crawled_data["content"].append(content.text)

                    # 把爬到的資料存進資料庫
                    save_data(crawled_data)

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
                get_card_info(card_url)
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
