import spacy
import re
import logging
from fuzzywuzzy import fuzz


class TextProcessor:
    def __init__(self):
        try:
            self.nlp = spacy.load("zh_core_web_md")
        except OSError:
            logging.error("無法載入 zh_core_web_md 模型")
            raise

    def clean_Space(self, content):
        clean_text = re.sub(r"\s+", " ", content)
        return clean_text.strip()

    def normalize_text(self, text):
        # 數字格式
        text = re.sub(r"百分之(\d+\.?\d*)", r"\1%", text)
        text = re.sub(r"(\d+\.?\d*)趴", r"\1%", text)

        # 貨幣格式
        text = re.sub(r"新台幣|新臺幣|台幣|臺幣", "NT$", text)
        text = re.sub(r"(\d+)元", r"NT$\1", text)

        # 去除空白
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def extract_sentences_with_keywords(self, text, keywords):
        # 關鍵字
        sentences = []
        doc = self.nlp(text)

        for sent in doc.sents:
            sent_text = sent.text.strip()
            contains_keyword = False

            for keyword in keywords:
                if keyword in sent_text:
                    contains_keyword = True
                    break

            if contains_keyword:
                sentences.append(sent_text)

        return sentences


class EntityExtractor:
    # 關鍵字

    def __init__(self):
        self.processor = TextProcessor()

        # 同義詞
        self.synonym_mapping = {
            "foreign_transaction": ["國外", "海外", "境外", "國際", "外幣", "外國"],
            "domestic_transaction": ["國內", "本土", "台灣", "境內", "台灣境內"],
            "ecommerce_shopping": ["網購", "線上購物", "電商", "網路消費", "網路購物"],
            "mobile_payment": ["行動支付", "手機支付", "數位支付", "電子支付"],
            "department_store": ["百貨", "百貨公司", "購物中心", "商場"],
            "convenience_store": ["便利商店", "7-11", "全家", "萊爾富", "OK"],
        }

        # 商家
        self.merchant_patterns = {
            "momo": ["momo", "富邦momo", "momo購物", "momo網"],
            "pchome": ["pchome", "pc home", "露天", "pc商店街", "pchome24h"],
            "shopee": ["蝦皮", "shopee", "蝦皮購物"],
            "yahoo": ["yahoo", "奇摩", "yahoo購物"],
            "uber": ["uber", "uber eats", "ubereats"],
            "foodpanda": ["foodpanda", "熊貓", "panda"],
            "netflix": ["netflix", "網飛"],
            "spotify": ["spotify"],
            "coupang": ["coupang", "酷彭"],
        }

    def extract_reward_rates(self, text):
        # 回饋資訊
        results = []

        # 回饋率
        patterns = [
            r"(\d+\.?\d*)%.*?回饋",
            r"回饋.*?(\d+\.?\d*)%",
            r"享.*?(\d+\.?\d*)%",
            r"(\d+\.?\d*)趴",
            r"百分之(\d+\.?\d*)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                rate = float(match.group(1))
                context = text[max(0, match.start() - 50) : match.end() + 50]

                results.append(
                    {
                        "rate": rate,
                        "context": context.strip(),
                        "pattern_used": pattern,
                        "position": match.span(),
                    }
                )

        return results

    def extract_merchants(self, text):
        # 商家資訊
        results = []

        for merchant_key, patterns in self.merchant_patterns.items():
            for pattern in patterns:
                if pattern.lower() in text.lower():
                    context_match = re.search(
                        f".{{0,50}}{re.escape(pattern)}.{{0,50}}", text, re.IGNORECASE
                    )
                    if context_match:
                        found_text = context_match.group(0).strip()
                        results.append(
                            {
                                "merchant_key": merchant_key,
                                "merchant_pattern": pattern,
                                "context": found_text,
                                "confidence": fuzz.ratio(
                                    pattern.lower(), found_text.lower()
                                ),
                            }
                        )

        return results

    def extract_conditions_and_limits(self, text):
        # 限制
        results = []

        limit_patterns = [
            r"上限.*?(\d+(?:,\d+)?).*?元",
            r"最高.*?(\d+(?:,\d+)?).*?元",
            r"不超過.*?(\d+(?:,\d+)?).*?元",
            r"(\d+(?:,\d+)?).*?元.*?上限",
        ]

        for pattern in limit_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                amount = match.group(1).replace(",", "")
                context = text[max(0, match.start() - 30) : match.end() + 30]
                results.append(
                    {
                        "type": "spending_limit",
                        "amount": int(amount),
                        "context": context.strip(),
                        "pattern_used": pattern,
                    }
                )

        time_patterns = [
            r"(\d{4})年(\d{1,2})月.*?前",
            r"活動期間.*?(\d{4}/\d{1,2}/\d{1,2}).*?(\d{4}/\d{1,2}/\d{1,2})",
            r"限時.*?(\d+)個月",
        ]

        for pattern in time_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                context = text[max(0, match.start() - 30) : match.end() + 30]
                results.append(
                    {
                        "type": "time_limit",
                        "time_info": match.groups(),
                        "context": context.strip(),
                        "pattern_used": pattern,
                    }
                )

        return results
