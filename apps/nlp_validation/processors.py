import spacy
import re
import logging


class TextProcessor:
    # 文字標準化處理器

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
            contains_keyword = False  # 預設沒有找到關鍵字

            for keyword in keywords:
                if keyword in sent_text:
                    contains_keyword = True
                    break  # 找到一個就可以停止

            if contains_keyword:
                sentences.append(sent_text)

        return sentences
