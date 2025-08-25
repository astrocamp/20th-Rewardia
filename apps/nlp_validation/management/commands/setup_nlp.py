from django.core.management.base import BaseCommand
import spacy
import re


class Command(BaseCommand):

    def handle(self, *args, **options):

        self.stdout.write(" NLP 系統初始化檢查\n")

        success = True

        # 檢查並測試 spaCy 模型
        if not self._check_and_test_spacy():
            success = False

        # 輸出結果
        if success:
            self.stdout.write(self.style.SUCCESS("\n NLP 系統就緒！"))
        else:
            self.stdout.write(self.style.ERROR("\n 系統未就緒，請先解決上述問題"))

    def _check_and_test_spacy(self):
        """檢查 spaCy 模型並測試基本功能"""

        models_to_check = [
            ("zh_core_web_md", "中文模型"),
            ("en_core_web_md", "英文模型"),
        ]

        for model_name, display_name in models_to_check:
            try:
                nlp = spacy.load(model_name)
                self.stdout.write(f"   {display_name} ({model_name}) 載入成功")

            except OSError:
                self.stdout.write(
                    self.style.ERROR(f"   {display_name} ({model_name}) 未安裝")
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"      請執行: python -m spacy download {model_name}"
                    )
                )
                return False

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   {display_name} 載入失敗: {str(e)}")
                )
                return False

        # 測試基本 NLP 功能
        self.stdout.write(" 測試基本 NLP 功能...")

        try:
            # 測試文字 - 信用卡相關內容
            test_text = "滙豐銀行匯鑽卡一般消費1%回饋，海外消費2.8%回饋，momo購物5.3%現金回饋，年費NT$2,000"

            # spaCy 處理
            nlp = spacy.load("zh_core_web_md")
            doc = nlp(test_text)
            entities_count = len(doc.ents)

            # 文字規則測試

            percentages = re.findall(r"(\d+(?:\.\d+)?)\s*%", test_text)
            amounts = re.findall(r"NT\$\s*(\d+(?:,\d+)?)", test_text)

            self.stdout.write(f"   文字處理成功")
            self.stdout.write(f"     - 實體識別: {entities_count} 個")
            self.stdout.write(f"     - 回饋率提取: {percentages}")
            self.stdout.write(f"     - 找到金額: {amounts}")

            # 基本驗證
            if len(percentages) >= 2:
                self.stdout.write("   回饋率識別正常")
                return True
            else:
                self.stdout.write(self.style.WARNING("  ️ 回饋率識別可能有問題"))
                return False

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   NLP 測試失敗: {str(e)}"))
            return False
