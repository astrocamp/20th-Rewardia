from selenium import webdriver
from selenium.webdriver.common.by import By
import random
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    StaleElementReferenceException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.relative_locator import locate_with
import time
from apps.card_crawler.models import CrawledData, CrawledRecord
from datetime import datetime

failed_cards = {}
processed_urls = set()
# 仿效真人操作瀏覽器，隨機從0.7-1.4秒之間，挑選暫停秒數
sleep_time = random.uniform(0.7, 1.4)


def save_data(data):
    content = ",".join(data["content"])
    card_img = data["card_img"]

    crawled_card, created = CrawledData.objects.update_or_create(
        url=data["url"],
        defaults={
            "content": content,
            "is_active": True,
            "card_img": card_img,
            "deleted_at": None,
        },
    )


# 將不存在於roo.cash且存在於我們db的url，設為刪除狀態
def handle_missing_urls(urls):
    CrawledData.objects.filter(is_active=True).exclude(url__in=urls).update(
        is_active=False, deleted_at=datetime.now()
    )


def create_error_data(url, error, card_name=None):
    return {
        "url": url,
        "error": error,
        "card_name": card_name if card_name else "Card not found.",
    }


# 抓一張卡的function
def get_card_info(driver, url):
    try:
        driver.get(url)
        print(f"Processing: {url}")

        try:
            # 找到卡的名字：中國信託 LINE Pay 信用卡
            card_name = driver.find_element(
                By.CSS_SELECTOR, 'h1[data-testid="product-title"]'
            ).text.strip()
            card_img = driver.find_element(
                By.CSS_SELECTOR, 'img[data-testid="product-logo"]'
            ).get_attribute("src")

            print(card_img)

        except WebDriverException as error:
            find_card_error = create_error_data(url, error)
            failed_cards.append(find_card_error)
            print(f"Error fetching card: {error}")

        try:
            # 找到navbar和footer之間的所有button
            buttons = driver.find_elements(
                locate_with(By.TAG_NAME, "button")
                .below({By.TAG_NAME: "h1"})
                .above({By.XPATH: "//h2[text()='其他推薦信用卡']"})
            )
            # action = ActionChains(driver)

            # 點選這些button，讓他們展開，因為資訊隱藏在裡面
            for button in buttons:
                try:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", button
                    )
                    time.sleep(0.5)
                    # 改成一個一個點按鈕好像比較有效，也比較不會漏點
                    button.click()

                # 為了忽略element移動找不到的錯誤，因為實際上還是點的到
                except StaleElementReferenceException:
                    continue

            try:
                # 比較節省時間的等待方式，如果元素在5秒內還沒出現就會回傳錯誤
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_all_elements_located((By.CLASS_NAME, "answer"))
                )
            except TimeoutException as error:
                print("Error fetching elements")
                answer_error = create_error_data(url, error, card_name=card_name)
                failed_cards.append(answer_error)

        except WebDriverException as error:
            print(f"Error fetching button: {error}")
            button_error = create_error_data(url, error, card_name=card_name)
            failed_cards.append(button_error)

        try:
            # 將抓取到的資料整理成字典
            crawled_data = {"url": url, "content": [], "card_img": card_img}

            driver.implicitly_wait(5)
            # 找到navbar和footer之間的所有h4, h5, li, p的元素
            contents = driver.find_elements(
                locate_with(By.CSS_SELECTOR, "h4,h5,li,p,p:not(li p)")
                .above({By.XPATH: "//h2[text()='其他推薦信用卡']"})
                .below({By.TAG_NAME: "h1"})
            )
            # 把它存到array
            crawled_data["content"].append(card_name)
            for content in contents:
                # 排出空白的
                if len(content.text) > 1:
                    crawled_data["content"].append(content.text)

            # 把爬到的資料存進資料庫
            save_data(crawled_data)

        except WebDriverException as error:
            print(f"Error finding content: {error}")
            tags_error = create_error_data(url, error, card_name=card_name)
            failed_cards.append(tags_error)

    except WebDriverException as error:
        print(f"Card not found: {error}")
        webpage_error = create_error_data(url, error)
        failed_cards.append(webpage_error)
        # 找不到卡，就終止這次的函式

    finally:
        print("Finished.")


# 把整個爬url的功能包成一個function
def crawl_roo_urls(driver):
    main_url_page = "https://roo.cash/creditcard/"

    try:
        driver.get(main_url_page)
        # 在尋找物件前要等多久
        driver.implicitly_wait(5)

        try:
            categories = driver.find_elements(
                By.CSS_SELECTOR, "a[type='button'][rel='opener']"
            )
            categories_urls = [
                category.get_attribute("href") for category in categories
            ]

            return categories_urls

        except WebDriverException as error:
            print(f"Error fetching element: {error}")

    except WebDriverException as error:
        print(f"Error fetching main page: {error}")


# 抓所有卡的function
def crawl_roo_cards(driver, cat_urls):
    try:
        # 先進到每一個類別的分頁，跳過第一個，因為第一個是2025年精選，那些一定分散在各個類別裡
        for url in cat_urls[1:]:
            driver.get(url)
            driver.implicitly_wait(2)
            card_names = driver.find_elements(
                By.CSS_SELECTOR, "a[data-testid='product-detail']"
            )
            card_urls = [card.get_attribute("href") for card in card_names]

            for card_url in card_urls:
                get_card_info(driver, card_url)
                time.sleep(sleep_time)
                processed_urls.add(card_url)

        # 排除成功的url，並將沒有被找到的url，設is_active=False
        handle_missing_urls(processed_urls)

    except WebDriverException as error:
        print(f"Error fetching page: {error}")

    finally:
        print(f"Failed or with error: {failed_cards}")


def save_crawl_record(data):
    CrawledRecord.objects.create(
        total_time=data["total_time"],
        total_cards=data["total_cards"],
        average_time=data["average_cards"],
        errors=data["errors"],
    )


# 寫這個目的是讓瀏覽器只要開一次，不要開開關關
def main_crawler():
    try:
        start_time = time.time()
        driver = webdriver.Chrome()
        category_urls = crawl_roo_urls(driver)
        crawl_roo_cards(driver, category_urls)
        total_time = time.time() - start_time

        crawl_record = {
            "total_time": total_time,
            "total_cards": len(processed_urls),
            "average_time": f"{(total_time / len(processed_urls)):.3f}",
            "errors": failed_cards,
        }

        save_crawl_record(crawl_record)

    except Exception as error:
        print(f"失敗: {error}")

    finally:
        print(
            f"總共載入了 {len(processed_urls)} 張卡片\n失敗卡片數：{len(failed_cards)}\n總測試時間: {time.strftime('%H:%M:%S', time.gmtime(total_time))}\n平均時間 {(total_time / len(processed_urls)):.3f} 秒/張，Done!"
        )
        driver.quit()


if __name__ == "__main__":
    main_crawler()
