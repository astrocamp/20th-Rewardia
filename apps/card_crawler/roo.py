from selenium import webdriver
from selenium.webdriver.common.by import By
import random
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.relative_locator import locate_with
import time
from apps.card_crawler.models import CrawledData, CrawledRecord
from datetime import timedelta
from django.utils import timezone
from datetime import datetime

failed_cards = {"failed": []}
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
        is_active=False, deleted_at=timezone.now()
    )


def create_error_data(url, error, card_name=None):
    return {
        "url": url,
        # 這裡只存取error的名字，因為error本身是object，所以無法存進JSONField
        "error": type(error).__name__,
        "card_name": card_name if card_name else "Card not found.",
    }


def find_card_buttons(driver):
    """查找信用卡頁面的按鈕"""
    return driver.find_elements(
        locate_with(By.CSS_SELECTOR, "button[type='button']")
        .below({By.TAG_NAME: "h1"})
        .above({By.XPATH: "//h2[text()='其他推薦信用卡']"})
    )


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

            contents = driver.find_elements(
                locate_with(By.CSS_SELECTOR, "h4,h5,li,p:not(li p)")
                .above({By.XPATH: "//h2[text()='其他推薦信用卡']"})
                .below({By.TAG_NAME: "h1"})
            )

            # 將抓取到的資料整理成字典
            crawled_data = {"url": url, "content": [], "card_img": card_img}
            crawled_data["content"].append(card_name)

            for content in contents:
                if len(content.text) > 1:
                    crawled_data["content"].append(content.text)

        except WebDriverException as error:
            find_card_error = create_error_data(url, error)
            failed_cards["failed"].append(find_card_error)
            print(f"Error fetching card: {error}")

        try:
            # 找到navbar和footer之間的所有button
            buttons = find_card_buttons(driver)

            # 點選這些button，讓他們展開，因為資訊隱藏在裡面
            for i, button in enumerate(buttons):
                try:
                    # 重新查找按鈕元素避免 stale reference
                    current_buttons = find_card_buttons(driver)
                    if i < len(current_buttons):
                        current_button = current_buttons[i]
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});",
                            current_button,
                        )
                        time.sleep(0.5)
                        # 使用 JavaScript 點擊避免元素被遮擋
                        driver.execute_script("arguments[0].click();", current_button)

                    try:
                        time.sleep(1)
                        answers = driver.find_elements(
                            locate_with(By.CLASS_NAME, "answer")
                            .above({By.XPATH: "//h2[text()='其他推薦信用卡']"})
                            .below({By.TAG_NAME: "h1"})
                        )
                        for answer in answers:
                            if answer and len(answer.text) > 1:
                                crawled_data["content"].append(answer.text)

                    # 為了忽略element移動找不到的錯誤，因為實際上還是點的到
                    except StaleElementReferenceException:
                        continue

                    except NoSuchElementException:
                        continue

                    except WebDriverException as error:
                        print(f"Error finding content: {error}")
                        tags_error = create_error_data(url, error, card_name=card_name)
                        failed_cards["failed"].append(tags_error)

                    # 打開了，再把它關起來，重新查找按鈕避免 stale reference
                    close_buttons = find_card_buttons(driver)
                    if i < len(close_buttons):
                        driver.execute_script("arguments[0].click();", close_buttons[i])

                except WebDriverException as error:
                    print(f"Error fetching button: {error}")
                    button_error = create_error_data(url, error, card_name=card_name)
                    failed_cards["failed"].append(button_error)

            save_data(crawled_data)
        except WebDriverException as error:
            print(f"Card not found: {error}")
            webpage_error = create_error_data(url, error)
            failed_cards["failed"].append(webpage_error)
            # 找不到卡，就終止這次的函式

    except WebDriverException as error:
        print(f"Error finding content: {error}")
        tags_error = create_error_data(url, error, card_name=card_name)
        failed_cards["failed"].append(tags_error)

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
            # 等待頁面完全載入
            time.sleep(1)

            categories = driver.find_elements(
                By.CSS_SELECTOR, "a[type='button'][rel='opener']"
            )

            # 立即提取所有 href 避免 stale element
            categories_urls = []
            for i, category in enumerate(categories):
                try:
                    href = category.get_attribute("href")
                    if href:
                        categories_urls.append(href)
                except Exception as e:
                    print(f"Error getting href for category {i}: {e}")
                    # 重新找元素
                    try:
                        fresh_categories = driver.find_elements(
                            By.CSS_SELECTOR, "a[type='button'][rel='opener']"
                        )
                        if i < len(fresh_categories):
                            href = fresh_categories[i].get_attribute("href")
                            if href:
                                categories_urls.append(href)
                    except:
                        continue

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
                try:
                    current_card = CrawledData.objects.get(url=card_url)
                    # 一小時內沒抓過的，就抓取，跳過一小時內抓過的
                    if timezone.now() - current_card.updated_at > timedelta(hours=24):
                        get_card_info(driver, card_url)
                        time.sleep(sleep_time)
                        processed_urls.add(card_url)
                    else:
                        # 就算沒有抓，還是算已經處理過的卡
                        processed_urls.add(card_url)
                        print("一天內已經抓過了。")
                # 如果這張卡不存在資料庫，那就繼續抓取
                except CrawledData.DoesNotExist:
                    get_card_info(driver, card_url)
                    time.sleep(sleep_time)
                    processed_urls.add(card_url)

        # 排除成功的url，並將沒有被找到的url，設is_active=False
        handle_missing_urls(processed_urls)

    except WebDriverException as error:
        print(f"Error fetching page: {error}")

    finally:
        print(f"Failed or with error: {failed_cards['failed']}")


def save_crawl_record(data):
    CrawledRecord.objects.create(
        total_time=data["total_time"],
        total_cards=data["total_cards"],
        average_time=data["average_time"],
        errors=data["errors"],
    )


# 寫這個目的是讓瀏覽器只要開一次，不要開開關關
def main_crawler():
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    options.set_preference("browser.cache.disk.enable", False)
    options.set_preference("browser.cache.memory.enable", False)
    options.set_preference("browser.sessionhistory.max_total_viewers", 0)
    options.set_preference("browser.display.use_system_colors", False)
    options.set_preference("extensions.enabled", False)
    options.set_preference("extensions.autoDisableScopes", 14)
    options.set_preference("network.http.use-cache", False)
    options.set_preference("network.dns.disableIPv6", True)
    options.set_preference("dom.ipc.processCount", 1)
    options.set_preference("browser.tabs.remote.autostart", False)
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    options.set_preference("webdriver.load.strategy", "unstable")
    options.set_preference(
        "general.useragent.override",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    )

    try:
        start_time = time.time()
        # 使用遠端 Selenium Grid
        driver = webdriver.Remote(
            command_executor="http://rewardia-selenium:4444", options=options
        )
        # driver = webdriver.Firefox(options=options)
        category_urls = crawl_roo_urls(driver)
        crawl_roo_cards(driver, category_urls)

    except Exception as error:
        print(f"失敗: {error}")
        breakpoint()

    finally:
        total_time = time.time() - start_time
        # 防止除零錯誤
        average_time = (
            total_time / len(processed_urls) if len(processed_urls) > 0 else 0
        )

        crawl_record = {
            "total_time": total_time,
            "total_cards": len(processed_urls),
            "average_time": average_time,
            "errors": failed_cards,
        }

        save_crawl_record(crawl_record)

        if len(processed_urls) > 0:
            print(
                f"總共載入了 {len(processed_urls)} 張卡片\n有誤卡片數：{len(failed_cards)}\n總測試時間: {time.strftime('%H:%M:%S', time.gmtime(total_time))}\n平均時間 {average_time:.3f} 秒/張，Done!"
            )
        else:
            print(
                f"沒有處理任何卡片\n有誤卡片數：{len(failed_cards)}\n總測試時間: {time.strftime('%H:%M:%S', time.gmtime(total_time))}\n無法計算平均時間，Done!"
            )
        driver.quit()


if __name__ == "__main__":
    main_crawler()
