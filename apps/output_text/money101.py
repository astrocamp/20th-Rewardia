from bs4 import BeautifulSoup
import requests

# money101 74張精選的網站
url = "https://www.money101.com.tw/%E4%BF%A1%E7%94%A8%E5%8D%A1/%E5%85%A8%E9%83%A8"
page = requests.get(url)
soup = BeautifulSoup(page.text,"html.parser")
# 找到相關的html tag
card_urls = soup.find_all('button',attrs={"data-property-key":"PRODUCT_BUTTON"})
# 擷取信用卡的名字
card_names = [card.get('data-property-url').replace("/信用卡/產品/","") for card in card_urls]

cards_dict = []
not_ok_card = []

for card in card_names:
    # 信用卡名字接在後面就是該卡片的頁面
    url = "https://www.money101.com.tw/信用卡/產品/" + f"{card}"
    page = requests.get(url)

    # 如果網站存在
    if page.status_code == 200:
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
    # 無法進入的網站/不存在的網站
    else:
        not_ok_card.append(card)


print(cards_dict)
print(not_ok_card)