import spacy
import re
import time
import json
from django.core.management.base import BaseCommand
from apps.nlp_validation.config import NLPConfig
from django.utils import timezone
from apps.cards.models import CreditCard
from apps.rewards.models import RewardCategory, PendingReward
from apps.nlp_validation.processors import (
    AdvancedTextCleaner,
    SmartSentenceSplitter,
    RewardContentFilter,
    SemanticClassifier,
    RewardRateExtractor,
    BankCardExtractor,
)


def load_config(config_path=None):
    return NLPConfig.load_config()


def check_existing_reward(card, nlp_category, nlp_scope, rate):
    """檢查是否已有相同的回饋規則"""
    existing = RewardCategory.objects.filter(
        card=card,
        # 這裡需要根據 nlp_category/scope 來判斷是否重複
        # 暫時先檢查是否有相同回饋率
    ).first()
    return existing


class Command(BaseCommand):
    help = "Run NLP validation processors and save results to PendingReward model"

    def handle(self, *args, **options):
        """主要處理邏輯"""
        self.stdout.write(self.style.SUCCESS("開始 NLP 驗證處理..."))

        config = load_config()

        cleaner = AdvancedTextCleaner(config)
        splitter = SmartSentenceSplitter(config)
        filter_obj = RewardContentFilter(config)
        classifier = SemanticClassifier(config)
        rate_extractor = RewardRateExtractor(config)
        bank_card_extractor = BankCardExtractor(config)

        json_file_path = config["settings"]["test_parameters"]["json_file_path"]

        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                card_data = json.load(f)

            test_cases = []
            min_cards = config["settings"]["test_parameters"]["min_test_cards"]
            max_cards = config["settings"]["test_parameters"]["max_test_cards"]
            for card in card_data[min_cards:max_cards]:
                if "content" in card:
                    test_cases.append(card["content"])

        except FileNotFoundError:
            self.stdout.write(self.style.WARNING("JSON檔案未找到，使用預設測試資料"))
            test_cases = config["settings"]["test_parameters"]["fallback_test_data"]

        total_start_time = time.time()

        for index, test_text in enumerate(test_cases, 1):
            index_start_time = time.time()
            self.stdout.write(f"開始處理：{index}")

            try:
                # 1. 文本清洗
                cleaned = cleaner.comprehensive_text_cleaning(test_text)

                # 2. 句子分割
                sentences = splitter.smart_sentence_split(cleaned)

                # 3. 提取銀行和信用卡名稱
                bank_card_info = bank_card_extractor.extract_bank_and_card(test_text)
                bank_name, card_name = bank_card_info

                # 4. 查找或建立 CreditCard
                credit_card = None
                if bank_name and card_name:
                    credit_card, created = CreditCard.objects.get_or_create(
                        name=card_name, bank=bank_name, defaults={"is_active": False}
                    )
                    if created:
                        self.stdout.write(f"建立新信用卡：{bank_name} {card_name}")

                if not credit_card:
                    self.stdout.write(
                        f"無法提取銀行或卡片名稱，跳過：{test_text[:50]}..."
                    )
                    continue

                # 5. 過濾回饋相關句子
                filtered = filter_obj.filter_reward_sentences(sentences)

                # 6. 去重處理
                unique_filtered = []
                deduplication_threshold = config["settings"]["deduplication_threshold"]

                if filtered:
                    filtered_docs = list(classifier.nlp.pipe(filtered, batch_size=50))
                    sentence_to_doc = dict(zip(filtered, filtered_docs))

                    for sentence, sentence_doc in zip(filtered, filtered_docs):
                        is_duplicate = False
                        for existing in unique_filtered:
                            existing_doc = sentence_to_doc[existing]
                            if sentence_doc.has_vector and existing_doc.has_vector:
                                similarity = sentence_doc.similarity(existing_doc)
                                if similarity >= deduplication_threshold:
                                    is_duplicate = True
                                    break
                            elif sentence == existing:
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            unique_filtered.append(sentence)

                # 7. 處理每個句子
                context_sentences = []
                for i, sent in enumerate(unique_filtered):
                    context_text = ""
                    if i > 0:
                        context_text += unique_filtered[i - 1]
                    context_text += sent
                    context_sentences.append((sent, context_text))

                if context_sentences:
                    main_sentences = [sent for sent, _ in context_sentences]
                    context_texts = [context for _, context in context_sentences]
                    main_docs = list(classifier.nlp.pipe(main_sentences, batch_size=50))
                    context_docs = list(
                        classifier.nlp.pipe(context_texts, batch_size=50)
                    )

                    for j, (sent, context_text) in enumerate(context_sentences, 1):
                        main_doc = main_docs[j - 1] if j - 1 < len(main_docs) else None
                        context_doc = (
                            context_docs[j - 1] if j - 1 < len(context_docs) else None
                        )

                        # 8. 語義分類
                        classification = classifier.classify_sentence_cached(
                            sent, context_text, main_doc, context_doc
                        )

                        # 9. 回饋率提取
                        rates = rate_extractor.extract_rates_from_sentence(sent)
                        results_list = rate_extractor.record_extraction_results(
                            sent, classification, rates
                        )

                        # 10. 建立 PendingReward 記錄
                        for result in results_list:
                            if result["rates_found"] > 0:
                                # 檢查是否已有相同規則 (避免重複)
                                existing = check_existing_reward(
                                    credit_card,
                                    result["category"],
                                    result["scope"],
                                    result["min_rate"] or result["max_rate"],
                                )

                                PendingReward.objects.create(
                                    card=credit_card,
                                    nlp_category=result["category"] or "未分類",
                                    nlp_scope=result["scope"] or "未知範圍",
                                    extracted_sentence=result["sentence"],
                                    confidence=result["confidence"],
                                    min_rate=result["min_rate"],
                                    max_rate=result["max_rate"],
                                    reward_type=result["reward_type"],
                                    status=PendingReward.Status.PENDING,
                                )

                self.stdout.write(
                    f"=========={index} Done! ====<-{(time.time() - index_start_time):.3f}->===="
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"處理失敗：{e}"))
                continue

        total_time = time.time() - total_start_time

        self.stdout.write(self.style.SUCCESS(f"\n總共載入ㄌ {len(test_cases)} 張卡片"))
        self.stdout.write(
            f"總測試時間: {time.strftime('%H:%M:%S', time.gmtime(total_time))}"
        )
        self.stdout.write(f"平均時間 {(total_time / len(test_cases)):.3f} 秒/張")
        self.stdout.write(self.style.SUCCESS("所有結果已儲存到 PendingReward 模型"))
