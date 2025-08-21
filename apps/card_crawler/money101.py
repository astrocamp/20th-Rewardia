from bs4 import BeautifulSoup
import requests
import time

# money101 74張精選的網站
url = "https://www.money101.com.tw/%E4%BF%A1%E7%94%A8%E5%8D%A1/%E5%85%A8%E9%83%A8"

try:
    # request會等待10秒的時間
    page = requests.get(url,timeout=10)
    # 出現4XX或5XX的錯誤時
    page.raise_for_status()
except requests.exceptions.RequestException as error:
    print(f"Error fetching main page: {error}")
    exit()

soup = BeautifulSoup(page.text,"html.parser")
try:
    # 找到相關的html tag
    card_urls = soup.find_all('button',attrs={"data-property-key":"PRODUCT_BUTTON"})
    # 擷取信用卡的名字
    card_names = [card.get('data-property-url').replace("/信用卡/產品/","") for card in card_urls]
except Exception as error:
    print(f"Error parsing main page: {error}")
    exit()

cards_dict = []
failed_cards = []

for card in card_names:
    # 信用卡名字接在後面就是該卡片的頁面
    url = "https://www.money101.com.tw/信用卡/產品/" + f"{card}"

    try:
        page = requests.get(url,timeout=10)
        page.raise_for_status()
        
        soup = BeautifulSoup(page.text,"html.parser")
        labels = soup.find_all('dt',class_='font-normal')
        label_text = [label.text.strip() for label in labels]
        contents = soup.find_all('dd',class_='type-label-sm')
        content_text = [content.text.strip().replace("\n\xa0","") for content in contents]

        company = soup.find('h3',string="發卡機構")
        card_type = soup.find('p',class_="type-label-sm md:type-label-md text-gray-11")

        card_dict = dict(zip(label_text,content_text))
        card_dict["name"] = soup.find('h1').text.strip()
        card_dict[f"{company.text}"] = card_type.text

        cards_dict.append(card_dict)

        time.sleep(0.5)

    # 幾個常見的錯誤，個別做except
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error for {card}: {e}")
        failed_cards.append(f"{card} - HTTP Error: {e}")
        
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error for {card}: {e}")
        failed_cards.append(f"{card} - Connection Error")
        
    except requests.exceptions.Timeout as e:
        print(f"Timeout error for {card}: {e}")
        failed_cards.append(f"{card} - Timeout")
        
    except requests.exceptions.RequestException as e:
        print(f"Request error for {card}: {e}")
        failed_cards.append(f"{card} - Request Error: {e}")
        
    except Exception as e:
        print(f"Unexpected error parsing {card}: {e}")
        failed_cards.append(f"{card} - Parse Error: {e}")



print(f"Successfully processed: {len(cards_dict)} cards")
print(f"Failed to process: {len(failed_cards)} cards")

if failed_cards:
    print("Failed cards:")
    for failed in failed_cards:
        print(f"  - {failed}")