import time
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from apps.nlp_validation.config import NLPConfig
from apps.cards.models import CreditCard
from apps.rewards.models import PendingReward
from apps.card_crawler.models import CrawledData
from apps.nlp_validation.models import AnalysisStatistics
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


class Command(BaseCommand):
    def handle(self, *args, **options):
        """主要處理邏輯"""
        self.stdout.write(self.style.SUCCESS("開始 NLP 驗證處理..."))

        with transaction.atomic():
            self._process_nlp_validation()

    def _process_nlp_validation(self):
        """實際的 NLP 驗證處理邏輯"""
        config = load_config()

        cleaner = AdvancedTextCleaner(config)
        splitter = SmartSentenceSplitter(config)
        filter_obj = RewardContentFilter(config)
        classifier = SemanticClassifier(config)
        rate_extractor = RewardRateExtractor(config)
        bank_card_extractor = BankCardExtractor(config)

        # 從 CrawledData 模型讀取所有爬蟲資料
        crawled_data = CrawledData.objects.filter(is_active=True).order_by("created_at")

        if not crawled_data.exists():
            self.stdout.write(self.style.WARNING("沒有找到爬蟲資料"))
            return

        test_cases = [data.content for data in crawled_data]

        # 初始化統計變數和快取
        total_start_time = time.time()
        error_info = []
        credit_card_cache = {}  # 快取已建立的信用卡

        # 預載入今天所有的 PendingReward 避免重複查詢
        today = timezone.now().date()
        existing_rewards = {}
        for reward in PendingReward.objects.filter(
            created_at__date=today, status=PendingReward.Status.PENDING
        ).select_related("card"):
            key = f"{reward.card.id}_{reward.nlp_category}_{reward.nlp_scope}_{reward.min_rate}_{reward.max_rate}"
            existing_rewards[key] = reward

        for index, test_text in enumerate(test_cases, 1):
            index_start_time = time.time()

            try:
                # 1. 文本清洗
                cleaned = cleaner.comprehensive_text_cleaning(test_text)

                # 2. 句子分割
                sentences = splitter.smart_sentence_split(cleaned)

                # 3. 提取銀行和信用卡名稱
                bank_card_info = bank_card_extractor.extract_bank_and_card(test_text)
                bank_name, card_name = bank_card_info

                # 4. 查找或建立 CreditCard（使用快取）
                credit_card = None
                if bank_name and card_name:
                    card_key = f"{bank_name}_{card_name}"

                    # 先檢查快取
                    if card_key in credit_card_cache:
                        credit_card = credit_card_cache[card_key]
                    else:
                        try:
                            credit_card, created = CreditCard.objects.get_or_create(
                                name=card_name,
                                bank=bank_name,
                                defaults={"is_active": False},
                            )
                            # 加入快取
                            credit_card_cache[card_key] = credit_card
                            if created:
                                self.stdout.write(
                                    f"建立新信用卡：{bank_name} {card_name}"
                                )
                        except ValidationError as e:
                            self.stdout.write(f"CreditCard驗證失敗: {e}")
                            self.stdout.write(
                                f"bank_name: '{bank_name}' (len: {len(bank_name)})"
                            )
                            self.stdout.write(
                                f"card_name: '{card_name}' (len: {len(card_name)})"
                            )
                            continue
                        except IntegrityError as e:
                            self.stdout.write(f"CreditCard完整性錯誤: {e}")
                            continue
                        except Exception as e:
                            self.stdout.write(f"CreditCard建立失敗: {e}")
                            continue

                if not credit_card:
                    self.stdout.write(
                        f"無法提取銀行或卡片名稱，跳過：{test_text[:50]}..."
                    )
                    continue

                # 5. 過濾回饋相關句子
                filtered = filter_obj.filter_reward_sentences(sentences)

                # 6. 去重處理
                unique_filtered = []
                seen_hashes = set()

                if filtered:
                    for sentence in filtered:
                        sentence_hash = hash(sentence)
                        if sentence_hash not in seen_hashes:
                            unique_filtered.append(sentence)
                            seen_hashes.add(sentence_hash)

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
                    # 優化批次處理效能

                    batch_size = int(os.environ.get("NLP_BATCH_SIZE", 50))
                    batch_size = min(batch_size, len(main_sentences))

                    main_docs = list(
                        classifier.nlp.pipe(main_sentences, batch_size=batch_size)
                    )
                    context_docs = list(
                        classifier.nlp.pipe(context_texts, batch_size=batch_size)
                    )

                    for j, (sent, context_text) in enumerate(context_sentences, 1):
                        # 8. 先檢查回饋率（快速過濾）
                        rates = rate_extractor.extract_rates_from_sentence(sent)

                        # 只有找到回饋率才做語義分類
                        if rates and len(rates) > 0:
                            main_doc = (
                                main_docs[j - 1] if j - 1 < len(main_docs) else None
                            )
                            context_doc = (
                                context_docs[j - 1]
                                if j - 1 < len(context_docs)
                                else None
                            )

                            # 9. 語義分類（只對有回饋率的句子）
                            classification = classifier.classify_sentence_cached(
                                sent, context_text, main_doc, context_doc
                            )
                        else:
                            # 沒有回饋率，跳過分類
                            classification = {"matches": []}

                        # 10. 記錄提取結果
                        results_list = rate_extractor.record_extraction_results(
                            sent, classification, rates
                        )

                        # 11. 建立 PendingReward 記錄
                        for result in results_list:
                            if result["rates_found"] > 0:
                                # 檢查是否已有相同規則 (避免重複)
                                reward_key = f"{credit_card.id}_{result['category']}_{result['scope']}_{result['min_rate']}_{result['max_rate']}"
                                existing = existing_rewards.get(reward_key)

                                if not existing:
                                    try:
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
                                    except Exception as e:
                                        error_msg = f"PendingReward建立失敗: {e}"
                                        error_info.append(
                                            {
                                                "index": index,
                                                "type": "PendingReward創建錯誤",
                                                "message": str(e),
                                                "details": {
                                                    "nlp_category": result.get(
                                                        "category"
                                                    ),
                                                    "nlp_scope": result.get("scope"),
                                                    "reward_type": result.get(
                                                        "reward_type"
                                                    ),
                                                },
                                            }
                                        )
                                        self.stdout.write(error_msg)
                                        self.stdout.write(
                                            f"nlp_category: '{result['category']}' (len: {len(str(result['category']) if result['category'] else '')})"
                                        )
                                        self.stdout.write(
                                            f"nlp_scope: '{result['scope']}' (len: {len(str(result['scope']) if result['scope'] else '')})"
                                        )
                                        self.stdout.write(
                                            f"reward_type: '{result['reward_type']}' (len: {len(str(result['reward_type']))})"
                                        )

                self.stdout.write(
                    f"=========={index} Done! ====<-{(time.time() - index_start_time):.3f}->===="
                )

            except Exception as e:
                error_info.append(
                    {
                        "index": index,
                        "type": "處理錯誤",
                        "message": str(e),
                        "text_preview": test_text[:100] + "..."
                        if len(test_text) > 100
                        else test_text,
                    }
                )
                self.stdout.write(self.style.ERROR(f"處理失敗：{e}"))
                continue

        total_time = time.time() - total_start_time

        self.stdout.write(self.style.SUCCESS(f"\n總共載入ㄌ {len(test_cases)} 張卡片"))
        self.stdout.write(
            f"總測試時間: {time.strftime('%H:%M:%S', time.gmtime(total_time))}"
        )
        self.stdout.write(f"平均時間 {(total_time / len(test_cases)):.3f} 秒/張")
        self.stdout.write(self.style.SUCCESS("所有結果已儲存到 PendingReward 模型"))

        # 創建分析統計記錄
        try:
            average_time = total_time / len(test_cases) if len(test_cases) > 0 else 0

            AnalysisStatistics.objects.create(
                total_time=total_time,
                analyzed_count=len(test_cases),
                average_time=average_time,
                errors={"errors": error_info, "error_count": len(error_info)},
            )

            self.stdout.write(self.style.SUCCESS("分析統計已記錄"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"統計記錄建立失敗: {e}"))
