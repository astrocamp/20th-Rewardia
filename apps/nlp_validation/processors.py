import spacy
import re
import logging


class TextProcessor:
    def __init__(self):
        try:
            self.nlp = spacy.load("zh_core_web_md")
        except OSError:
            logging.error("無法載入 zh_core_web_md 模型")
            raise

    def clean_space(self, content):
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
            if any(keyword in sent_text for keyword in keywords):
                sentences.append(sent_text)

        return sentences

    def filter_relevant_content(self, text):
        # 精簡內容
        keywords = [
            "回饋",
            "現金",
            "點數",
            "%",
            "趴",
            "消費",
            "刷卡",
            "海外",
            "國外",
            "境外",
            "國內",
            "網購",
            "momo",
            "蝦皮",
            "pchome",
            "uber",
            "netflix",
            "上限",
            "年費",
        ]

        relevant_sentences = self.extract_sentences_with_keywords(text, keywords)
        return " ".join(relevant_sentences)


class EntityExtractor:
    # 關鍵字

    def __init__(self):
        self.processor = TextProcessor()

        # 同義詞/回饋類別
        self.category_mapping = {
            "foreign_transaction": ["國外", "海外", "境外", "國際", "外幣", "外國"],
            "domestic_transaction": ["國內", "本土", "台灣", "境內", "台灣境內"],
            "ecommerce_shopping": ["網購", "線上購物", "電商", "網路消費", "網路購物"],
            "mobile_payment": ["行動支付", "手機支付", "數位支付", "電子支付"],
            "department_store": ["百貨", "百貨公司", "購物中心", "商場"],
            "convenience_store": ["便利商店", "7-11", "全家", "萊爾富", "OK"],
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

        # 電商
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

    def identify_category_from_context(self, context):
        # 用前後文分類類別
        for category, keywords in self.category_mapping.items():
            for keyword in keywords:
                if keyword in context:
                    return category

        return None

    def identify_merchant_from_context(self, context):
        # 用前後文分類電商
        context_lower = context.lower()
        for merchant, patterns in self.merchant_patterns.items():
            for pattern in patterns:
                if pattern.lower() in context_lower:
                    return merchant
        return None

    def extract_reward_rates(self, text):
        # 資訊處裡
        text = re.sub(r"(\d+\.?\d*)\s*\n\s*%", r"\1%", text)
        text = re.sub(r"(\d+\.?\d*)\s{2,}%", r"\1%", text)
        # 回饋資訊
        results = []
        seen_combinations = set()
        # 回饋率
        patterns = [
            r"(\d+\.?\d*)%.*?回饋",
            r"回饋.*?(\d+\.?\d*)%",
            r"享.*?(\d+\.?\d*)%",
            r"(\d+\.?\d*)趴",
            r"百分之(\d+\.?\d*)",
            r"消費.*?(\d+\.?\d*)%",
            r"為(\d+\.?\d*)%.*?回饋",
            r"(\d+\.?\d*)%現金",
            r"(\d+\.?\d*)%回",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                rate = float(match.group(1))
                if not (0 < rate <= 20):
                    continue

                context = text[max(0, match.start() - 0) : match.end()].strip()

                category = self.identify_category_from_context(context)
                merchant = self.identify_merchant_from_context(context)

                combination_key = (rate, category, merchant)
                if combination_key not in seen_combinations:
                    seen_combinations.add(combination_key)

                    results.append(
                        {
                            "rate": rate,
                            "context": context,
                            "category": category,
                            "merchant": merchant,
                        }
                    )

        return results

    def extract_merchants(self, text):
        # 商家資訊
        found_merchants = []

        for merchant_key, patterns in self.merchant_patterns.items():
            if any(pattern.lower() in text.lower() for pattern in patterns):
                found_merchants.append(merchant_key)

        return found_merchants

    def extract_categories(self, text):
        # 消費分類
        found_categories = []

        for category_key, keywords in self.category_mapping.items():
            if any(keyword in text for keyword in keywords):
                found_categories.append(category_key)

        return found_categories

    def extract_limits(self, text):
        # 限制
        patterns = [
            r"上限.*?(\d+(?:,\d+)?)",
            r"最高.*?(\d+(?:,\d+)?)",
            r"不超過.*?(\d+(?:,\d+)?)",
        ]

        amounts = []

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                amount = int(match.replace(",", ""))
                amounts.append(amount)

        return amounts

    def extract_all_info(self, raw_text):
        # 回收
        relevant_text = self.processor.filter_relevant_content(raw_text)
        normalized_text = self.processor.normalize_text(relevant_text)

        return {
            "reward_rates": self.extract_reward_rates(normalized_text),
            "merchants": self.extract_merchants(normalized_text),
            "categories": self.extract_categories(normalized_text),
            "spending_limits": self.extract_limits(normalized_text),
            "processed_text": relevant_text[:500] + "..."
            if len(relevant_text) > 500
            else relevant_text,
        }
