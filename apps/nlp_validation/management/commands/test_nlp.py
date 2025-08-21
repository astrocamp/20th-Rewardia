from django.core.management.base import BaseCommand
import spacy
import re

class Command(BaseCommand):
    help = 'Test NLP basic functionality'
    
    def add_arguments(self, parser):
        parser.add_argument('--text', type=str, help='Text to analyze')
        parser.add_argument('--file', type=str, help='File to analyze')
    
    def handle(self, *args, **options):
        self.stdout.write(" 開始 NLP 測試\n")
        
        try:
            # 測試 spaCy 載入
            nlp = spacy.load("zh_core_web_md")
            self.stdout.write(" spaCy 中文模型載入成功")
            
            # 決定要分析的文字
            if options['text']:
                text = options['text']
                self.stdout.write(f" 分析指定文字: {text[:50]}...")
            elif options['file']:
                try:
                    with open(options['file'], 'r', encoding='utf-8') as f:
                        text = f.read()
                    self.stdout.write(f" 分析檔案: {options['file']}")
                except FileNotFoundError:
                    self.stdout.write(f" 找不到檔案: {options['file']}")
                    return
            else:
                # 預設測試文字
                text = """滙豐銀行匯鑽卡一般消費 1%回饋無上限，
                行動支付/網購外送 3%回饋，年費 NT$ 2,000，首年免年費"""
                self.stdout.write("📝 使用預設測試文字")
            
            # NLP 分析
            doc = nlp(text[:1000])  # 只分析前1000字
            
            # 顯示實體識別結果
            self.stdout.write("\n spaCy 實體識別：")
            entities_found = False
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'MONEY', 'CARDINAL', 'PERSON']:
                    self.stdout.write(f"  {ent.text} -> {ent.label_}")
                    entities_found = True
            
            if not entities_found:
                self.stdout.write("  (未找到相關實體)")
            
            # 正規表達式分析
            self.stdout.write("\n 正規表達式分析：")
            
            # 找回饋率
            rates = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
            if rates:
                self.stdout.write(f"  回饋率: {rates}")
            
            # 找年費
            fees = re.findall(r'(?:年費|NT\$)\s*(\d+(?:,\d+)?)', text)
            if fees:
                self.stdout.write(f"  年費: {fees}")
            
            # 找銀行名稱
            banks = re.findall(r'(滙豐|中信|國泰|玉山|台新|富邦|第一|合庫|兆豐|永豐)(?:銀行)?', text)
            if banks:
                self.stdout.write(f"  銀行: {list(set(banks))}")
            
            # 找卡片名稱
            cards = re.findall(r'((?:匯鑽|御璽|現金回饋|Live|鑽金|白金|無限)卡?)', text)
            if cards:
                self.stdout.write(f"  卡片: {list(set(cards))}")
                
        except OSError as e:
            self.stdout.write(f" spaCy 模型載入失敗: {e}")
            self.stdout.write("💡 請執行: uv run python -m spacy download zh_core_web_md")
        except Exception as e:
            self.stdout.write(f" 執行錯誤: {e}")
        
        self.stdout.write("\n 測試完成！")