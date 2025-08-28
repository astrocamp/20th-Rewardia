import spacy
import re
import time
import json
from config import NLPConfig


def load_config(config_path=None):
    return NLPConfig.load_config()


class AdvancedTextCleaner:
    """文本清洗"""

    def clean_whitespace_and_newlines(self, text):
        """清空格換行"""
        cleaned = re.sub(r"\s+", " ", text)
        return cleaned.strip()

    def normalize_currency_terms(self, text):
        """新台幣/台幣/元 → NT$"""
        text = re.sub(r"(\d+\.?\d*)元", r"NT$\1", text)
        text = re.sub(r"新台幣|新臺幣|台幣|臺幣", "NT$", text)

        return text

    def normalize_percentage_terms(self, text):
        """統一百分比"""
        text = re.sub(r"百分之(\d+\.?\d*)", r"\1%", text)
        text = re.sub(r"百分之二點五", "2.5%", text)
        text = re.sub(r"百分之三", "3%", text)
        text = re.sub(r"百分之五", "5%", text)
        text = re.sub(r"(\d+\.?\d*)趴", r"\1%", text)
        # 分離的百分比
        text = re.sub(r"(\d+\.?\d*)\s*\n\s*%", r"\1%", text)
        text = re.sub(r"(\d+\.?\d*)\s{2,}%", r"\1%", text)

        return text

    def normalize_punctuation_to_fullwidth(self, text):
        """將標點符號轉換為全形"""
        text = re.sub(r"\.(?!\d)", "。", text)
        max_iterations = 2
        iteration_count = 0

        while re.search(r"(\d+),(\d{3})", text) and iteration_count < max_iterations:
            text = re.sub(r"(\d+),(\d{3})", r"\1\2", text)
            iteration_count += 1

        config = load_config()
        punctuation_map = config["punctuation_map"]

        for half, full in punctuation_map.items():
            text = text.replace(half, full)

        return text

    def remove_unnecessary_symbols(self, text):
        """移除符號"""
        config = load_config()
        unnecessary_symbols_regex = config["unnecessary_symbols_regex"]
        text = re.sub(unnecessary_symbols_regex, "", text)

        return text

    def comprehensive_text_cleaning(self, text):
        """清洗流程"""
        text = self.remove_unnecessary_symbols(text)

        text = self.clean_whitespace_and_newlines(text)

        text = self.normalize_currency_terms(text)

        text = self.normalize_percentage_terms(text)

        text = self.normalize_punctuation_to_fullwidth(text)

        text = re.sub(r"NT\$NT\$", "NT$", text)

        return text


class SmartSentenceSplitter:
    """標點符號分段"""

    def __init__(self, config_path=None):
        config = load_config(config_path)

        self.sentence_endings = config["sentence_endings"]
        self.min_sentence_length = config["settings"]["min_sentence_length"]

    def split_by_comma_with_merge(self, text):
        """中介符號切句子"""
        parts = [p.strip() for p in text.split("，") if p.strip()]
        if not parts:
            return []

        merged_sentences = []
        current_sentence = ""

        for part in parts:
            if not current_sentence:
                current_sentence = part
            else:
                if len(part) < self.min_sentence_length:
                    current_sentence += "，" + part
                else:
                    merged_sentences.append(current_sentence)
                    current_sentence = part

        if current_sentence:
            merged_sentences.append(current_sentence)

        return merged_sentences

    def split_by_ending_punctuation(self, text):
        """結束符號切句子"""
        sentences = []
        current_sentence = ""

        for char in text:
            current_sentence += char
            if char in self.sentence_endings:
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""

        # 如果沒有符號
        if current_sentence.strip():
            sentences.append(current_sentence.strip())

        return sentences

    def smart_sentence_split(self, text):
        """切句子流程"""
        primary_sentences = self.split_by_ending_punctuation(text)

        final_sentences = []
        for sentence in primary_sentences:
            comma_split = self.split_by_comma_with_merge(sentence)
            final_sentences.extend(comma_split)

        return final_sentences


class RewardContentFilter:
    """保留含有回饋句子"""

    def __init__(self, config_path=None):
        config = load_config(config_path)

        self.reward_keywords = config["reward_keywords"]["_keywords"]

        self.exclude_keywords = config["exclude_keywords"]["_keywords"]

        self.physical_store_keywords = config["physical_store_keywords"]["_keywords"]

    def contains_reward_indicators(self, sentence):
        return any(keyword in sentence for keyword in self.reward_keywords)

    def contains_exclude_indicators(self, sentence):
        return any(keyword in sentence for keyword in self.exclude_keywords)

    def contains_physical_store_indicators(self, sentence):
        return any(keyword in sentence for keyword in self.physical_store_keywords)

    def filter_reward_sentences(self, sentences):
        """保留回饋資訊句子流程"""
        filtered_sentences = []

        for sentence in sentences:
            if not self.contains_reward_indicators(sentence):
                continue

            if self.contains_exclude_indicators(sentence):
                continue

            if self.contains_physical_store_indicators(sentence):
                continue

            filtered_sentences.append(sentence)

        return filtered_sentences


class SemanticClassifier:
    """spaCy語義分類"""

    def __init__(self, config_path=None):
        config = load_config(config_path)

        try:
            self.nlp = spacy.load("zh_core_web_md")
        except OSError as e:
            print(f"載入 zh_core_web_md 失敗: {e}")
            print("請確認已安裝中文模型: python -m spacy download zh_core_web_md")
            raise

        # Category/Scope 語義種子詞
        self.category_scope_seeds = config["category_scope_seeds"]

        self.similarity_threshold = config["settings"]["similarity_threshold"]

        # 信心度設定
        self.confidence_scores = config["settings"]["confidence_scores"]

        # 擴展模式
        self.auto_expand_patterns = config["auto_expand_patterns"]

        # 關鍵詞擴展設定
        self.smart_expansion_enabled = config["settings"].get(
            "smart_keyword_expansion", True
        )
        self.expansion_similarity_threshold = config["settings"].get(
            "expansion_similarity_threshold", 0.7
        )

        self.domain_synonyms = config["domain_synonyms"]
        self.keyword_variations = config["keyword_variations"]

        # 預先所有種子詞
        if self.smart_expansion_enabled:
            self._expand_all_keywords()

    def find_semantic_match(self, text, threshold=None):
        """使用語義相似度找最佳category 和 scope"""
        if threshold is None:
            threshold = self.similarity_threshold

        text_doc = self.nlp(text)
        best_category = None
        best_scope = None
        best_score = 0

        for category, scopes in self.category_scope_seeds.items():
            for scope, seeds in scopes.items():
                for seed in seeds:
                    if seed in text:
                        # 直接匹配
                        return category, scope, self.confidence_scores["direct_match"]

                    # 相似度匹配
                    seed_doc = self.nlp(seed)
                    if text_doc.has_vector and seed_doc.has_vector:
                        similarity = text_doc.similarity(seed_doc)
                        if similarity > threshold and similarity > best_score:
                            best_score = similarity
                            best_category = category
                            best_scope = scope

        return best_category, best_scope, best_score

    def find_all_semantic_matches(self, text, threshold=None):
        """找出可能匹配支援多分類"""
        if threshold is None:
            threshold = self.similarity_threshold

        text_doc = self.nlp(text)
        direct_matches = []
        semantic_matches = []

        # 組合詞
        if "國內外" in text or "國內國外" in text:
            direct_matches.append(
                {
                    "category": "一般消費",
                    "scope": "國內",
                    "confidence": self.confidence_scores["direct_match"],
                }
            )
            direct_matches.append(
                {
                    "category": "一般消費",
                    "scope": "海外",
                    "confidence": self.confidence_scores["direct_match"],
                }
            )

        for category, scopes in self.category_scope_seeds.items():
            for scope, seeds in scopes.items():
                best_score_for_this_scope = 0
                matched_directly = False

                for seed in seeds:
                    if seed in text:
                        # 直接匹配
                        direct_matches.append(
                            {
                                "category": category,
                                "scope": scope,
                                "confidence": self.confidence_scores["direct_match"],
                            }
                        )
                        matched_directly = True
                        break

                    # 相似度匹配
                    if not matched_directly:
                        seed_doc = self.nlp(seed)
                        if text_doc.has_vector and seed_doc.has_vector:
                            similarity = text_doc.similarity(seed_doc)
                            if (
                                similarity > threshold
                                and similarity > best_score_for_this_scope
                            ):
                                best_score_for_this_scope = similarity

                # 沒直接匹配但有語義匹配加入語義匹配
                if not matched_directly and best_score_for_this_scope > 0:
                    semantic_matches.append(
                        {
                            "category": category,
                            "scope": scope,
                            "confidence": best_score_for_this_scope,
                        }
                    )

        # 直接匹配>語義匹配
        if direct_matches:
            all_matches = direct_matches
        else:
            # >0.8
            all_matches = [m for m in semantic_matches if m["confidence"] > 0.8]

        # 移除重複category+scope
        seen = set()
        unique_matches = []
        for match in all_matches:
            key = (match["category"], match["scope"])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)

        all_matches = unique_matches

        # 信心度排序
        all_matches.sort(key=lambda x: x["confidence"], reverse=True)
        return all_matches

    def _expand_all_keywords(self):
        """擴展關鍵詞"""
        print("正在進關鍵詞擴展...")
        expansion_count = 0

        for category, scopes in self.category_scope_seeds.items():
            for scope, seeds in scopes.items():
                original_count = len(seeds)
                expanded_seeds = self._expand_keyword_list(seeds)
                self.category_scope_seeds[category][scope] = expanded_seeds
                expansion_count += len(expanded_seeds) - original_count

        print(f"智能擴展完成，新增 {expansion_count} 個關鍵詞")

    def _expand_keyword_list(self, keywords):
        """單個關鍵詞"""
        expanded = set(keywords)  # 避免重複

        for keyword in keywords:
            similar_words = self._find_similar_words(keyword)
            expanded.update(similar_words)

        return list(expanded)

    def _find_similar_words(self, keyword):
        """用spaCy相似"""
        try:
            keyword_doc = self.nlp(keyword)
            if not keyword_doc.has_vector:
                return []

            domain_synonyms = self.domain_synonyms

            # 是否有預定義的同義詞
            similar_words = []
            for key, synonyms in domain_synonyms.items():
                if key in keyword or keyword in key:
                    similar_words.extend(synonyms)

            # 沒有預定試語義相似度
            if not similar_words and len(keyword) >= 2:
                variations = []
                for variation_func in self.keyword_variations:
                    result = variation_func(keyword)
                    if result:
                        variations.append(result)
                similar_words = [v for v in variations if v and v != keyword]

            # 限制擴展量
            return similar_words[:3]

        except Exception:
            return []

    # TODO: to config
    def auto_expand_category_keywords(self, text):
        """自動分類關鍵詞"""
        for group, keywords in self.auto_expand_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    if group == "海外":
                        return "一般消費", "海外"
                    elif group == "線上":
                        return "網購", "其他平台"
                    elif group == "交通":
                        return "交通/加油", "大眾運輸"
                    elif group == "行動支付":
                        return "交通/加油", "行動支付"

        return None, None

    def classify_sentence(self, sentence, context_text=None):
        """多重 category/scope 分類"""
        all_matches = []

        # 主句匹配
        matches = self.find_all_semantic_matches(sentence)
        all_matches.extend(matches)

        # 參考前後文
        if len(all_matches) == 0 and context_text:
            context_matches = self.find_all_semantic_matches(context_text)
            all_matches.extend(context_matches)

        # 試自動擴展 主句>context
        if not all_matches:
            category, scope = self.auto_expand_category_keywords(sentence)
            if category:
                all_matches.append(
                    {
                        "category": category,
                        "scope": scope,
                        "confidence": self.confidence_scores["auto_expand"],
                    }
                )
            elif context_text:
                category, scope = self.auto_expand_category_keywords(context_text)
                if category:
                    all_matches.append(
                        {
                            "category": category,
                            "scope": scope,
                            "confidence": self.confidence_scores["auto_expand"],
                        }
                    )

        # 預設None
        if not all_matches:
            all_matches.append(
                {
                    "category": None,
                    "scope": None,
                    "confidence": self.confidence_scores["default_classification"],
                }
            )

        return {
            "matches": all_matches,
            "sentence": sentence,
        }

    def classify_sentence_cached(
        self, sentence, context_text=None, main_doc=None, context_doc=None
    ):
        """向量分類"""
        all_matches = []

        # 找匹配
        matches = self.find_all_semantic_matches_cached(sentence, main_doc)
        all_matches.extend(matches)

        # 參考前後文
        if len(all_matches) == 0 and context_text and context_doc:
            context_matches = self.find_all_semantic_matches_cached(
                context_text, context_doc
            )
            all_matches.extend(context_matches)

        # 自動擴展 主句>context
        if not all_matches:
            category, scope = self.auto_expand_category_keywords(sentence)
            if category:
                all_matches.append(
                    {
                        "category": category,
                        "scope": scope,
                        "confidence": self.confidence_scores["auto_expand"],
                    }
                )
            elif context_text:
                category, scope = self.auto_expand_category_keywords(context_text)
                if category:
                    all_matches.append(
                        {
                            "category": category,
                            "scope": scope,
                            "confidence": self.confidence_scores["auto_expand"],
                        }
                    )

        # 設為預設None
        if not all_matches:
            all_matches.append(
                {
                    "category": None,
                    "scope": None,
                    "confidence": self.confidence_scores["default_classification"],
                }
            )

        return {
            "matches": all_matches,
            "sentence": sentence,
        }

    def find_all_semantic_matches_cached(self, text, text_doc=None, threshold=None):
        """使用向量語義匹配"""
        if threshold is None:
            threshold = self.similarity_threshold

        if text_doc is None:
            text_doc = self.nlp(text)

        direct_matches = []
        semantic_matches = []

        if "國內外" in text or "國內國外" in text:
            direct_matches.append(
                {
                    "category": "一般消費",
                    "scope": "國內",
                    "confidence": self.confidence_scores["direct_match"],
                }
            )
            direct_matches.append(
                {
                    "category": "一般消費",
                    "scope": "海外",
                    "confidence": self.confidence_scores["direct_match"],
                }
            )

        for category, scopes in self.category_scope_seeds.items():
            for scope, seeds in scopes.items():
                best_score_for_this_scope = 0
                matched_directly = False

                for seed in seeds:
                    if seed in text:
                        # 直接匹配
                        direct_matches.append(
                            {
                                "category": category,
                                "scope": scope,
                                "confidence": self.confidence_scores["direct_match"],
                            }
                        )
                        matched_directly = True
                        break

                    # 相似度匹配
                    if not matched_directly and text_doc.has_vector:
                        seed_doc = self.nlp(seed)
                        if seed_doc.has_vector:
                            similarity = text_doc.similarity(seed_doc)
                            if (
                                similarity > threshold
                                and similarity > best_score_for_this_scope
                            ):
                                best_score_for_this_scope = similarity

                # 沒直接匹配有語義匹配加語義候選
                if not matched_directly and best_score_for_this_scope > 0:
                    semantic_matches.append(
                        {
                            "category": category,
                            "scope": scope,
                            "confidence": best_score_for_this_scope,
                        }
                    )

        # 直接匹配>信心度匹配
        if direct_matches:
            all_matches = direct_matches
        else:
            # >0.8
            all_matches = [m for m in semantic_matches if m["confidence"] > 0.8]

        # 除重複 category+scope
        seen = set()
        unique_matches = []
        for match in all_matches:
            key = (match["category"], match["scope"])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)

        all_matches = unique_matches

        # 信心度排序
        all_matches.sort(key=lambda x: x["confidence"], reverse=True)
        return all_matches


class RewardRateExtractor:
    """回饋率提取"""

    def __init__(self, config_path=None):
        config = load_config(config_path)

        self.reward_patterns = config["reward_patterns"]["_patterns"]
        self.rate_range = config["settings"]["rate_range"]
        self.reward_type_keywords = config["reward_type_keywords"]

    def extract_rates_from_sentence(self, sentence):
        """提取回饋率"""
        rates = []

        for pattern in self.reward_patterns:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                try:
                    if match.lastindex and match.lastindex >= 1 and match.group(1):
                        rate = float(match.group(1))
                        if self.rate_range["min"] <= rate <= self.rate_range["max"]:
                            rates.append(
                                {
                                    "rate": rate,
                                    "matched_text": match.group(0),
                                    "pattern": pattern,
                                    "position": match.span(),
                                }
                            )
                except (ValueError, IndexError, AttributeError):
                    continue

        return rates

    def detect_reward_type(self, sentence):
        """檢測回饋類型"""
        for reward_type, keywords in self.reward_type_keywords.items():
            if reward_type == "_description":
                continue
            for keyword in keywords:
                if keyword in sentence:
                    return reward_type
        return "unknown"

    def record_extraction_results(self, sentence, classification, rates):
        """記錄結果"""
        reward_type = self.detect_reward_type(sentence)

        if not rates:
            results = []
            for match in classification["matches"]:
                results.append(
                    {
                        "sentence": sentence,
                        "category": match["category"],
                        "scope": match["scope"],
                        "confidence": match["confidence"],
                        "rates_found": 0,
                        "all_rates": [],
                        "min_rate": None,
                        "max_rate": None,
                        "reward_type": reward_type,
                        "rate_details": [],
                    }
                )
            return results

        all_rate_values = [r["rate"] for r in rates]

        # 檢查最高關鍵詞
        has_max_keyword = "最高" in sentence

        min_rate = None
        max_rate = None

        if has_max_keyword:
            # 分析語意
            if len(set(all_rate_values)) > 1:
                # 數字最大為max其他為min
                max_val = max(all_rate_values)
                min_vals = [r for r in all_rate_values if r != max_val]
                min_rate = min(min_vals) if min_vals else None
                max_rate = max_val
            else:
                # 最高記為max
                max_rate = all_rate_values[0]
        else:
            # 沒最高預設為min
            min_rate = min(all_rate_values)

        results = []
        for match in classification["matches"]:
            results.append(
                {
                    "sentence": sentence,
                    "category": match["category"],
                    "scope": match["scope"],
                    "confidence": match["confidence"],
                    "rates_found": len(rates),
                    "all_rates": all_rate_values,
                    "min_rate": min_rate,
                    "max_rate": max_rate,
                    "reward_type": reward_type,
                    "rate_details": rates,
                }
            )

        return results


def test_processors_11():
    cleaner = AdvancedTextCleaner()
    splitter = SmartSentenceSplitter()
    filter_obj = RewardContentFilter()
    classifier = SemanticClassifier()
    rate_extractor = RewardRateExtractor()

    config = load_config()

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
        print("JSON檔案未找到，使用預設測試資料")
        test_cases = config["settings"]["test_parameters"]["fallback_test_data"]

    results = []
    total_start_time = time.time()

    for index, test_text in enumerate(test_cases, 1):
        index_start_time = time.time()
        print(f"開始處理：{index}")
        # print(" ")
        # print(f"原始文本: \n{test_text}")
        # print(" ")

        cleaned = cleaner.comprehensive_text_cleaning(test_text)

        sentences = splitter.smart_sentence_split(cleaned)
        sentences_text = []
        # print("\n切割後句子:")
        for j, sent in enumerate(sentences, 1):
            sentence_text = f"  {j}. {sent}"
            sentences_text.append(sentence_text)
            # print(f"  {j}. {sent}")

        filtered = filter_obj.filter_reward_sentences(sentences)

        unique_filtered = []
        deduplication_threshold = config["settings"]["deduplication_threshold"]

        if not filtered:
            unique_filtered = []
        else:
            filtered_docs = list(classifier.nlp.pipe(filtered, batch_size=50))

            for i, (sentence, sentence_doc) in enumerate(zip(filtered, filtered_docs)):
                is_duplicate = False

                for j, existing in enumerate(unique_filtered):
                    existing_doc = filtered_docs[filtered.index(existing)]

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

        # print("\n過濾後:")
        filtereds_text = []
        for j, sent in enumerate(unique_filtered, 1):
            filtered_text = f"{j}. : {sent}"
            filtereds_text.append(filtered_text)
            # print(f"  {j}. {sent}")
        # print(
        #     f"去重前: {len(filtered)} 句，去重後: {len(unique_filtered)} 句 (閾值: {deduplication_threshold})"
        # )

        context_sentences = []
        for i, sent in enumerate(unique_filtered):
            context_text = ""
            if i > 0:
                context_text += unique_filtered[i - 1]
            context_text += sent
            # if i < len(unique_filtered) - 1:
            #     context_text += unique_filtered[i + 1]
            context_sentences.append((sent, context_text))

        # print("\n語義分類和回饋率提取結果:")
        all_results = []
        uniques = []

        main_sentences = [sent for sent, _ in context_sentences]
        context_texts = [context for _, context in context_sentences]

        if main_sentences:
            main_docs = list(classifier.nlp.pipe(main_sentences, batch_size=50))
            context_docs = list(classifier.nlp.pipe(context_texts, batch_size=50))
        else:
            main_docs = []
            context_docs = []

        for j, (sent, context_text) in enumerate(context_sentences, 1):
            main_doc = main_docs[j - 1] if j - 1 < len(main_docs) else None
            context_doc = context_docs[j - 1] if j - 1 < len(context_docs) else None

            classification = classifier.classify_sentence_cached(
                sent, context_text, main_doc, context_doc
            )
            rates = rate_extractor.extract_rates_from_sentence(sent)
            results_list = rate_extractor.record_extraction_results(
                sent, classification, rates
            )

            for result in results_list:
                if result["rates_found"] > 0:
                    all_results.append(result)

                    rate_info = []
                    if result["min_rate"] is not None:
                        rate_info.append(f"min: {result['min_rate']}%")
                    if result["max_rate"] is not None:
                        rate_info.append(f"max: {result['max_rate']}%")

                    unique = [
                        f"  {len(all_results)}. {result['category']} > {result['scope']} (信心度: {result['confidence']:.2f})",
                        f"     回饋率: {' | '.join(rate_info)} | 類型: {result['reward_type']}",
                        f"     句子: {context_text}",
                    ]
                    uniques.append(unique)

        result = {
            f"測試案例{index}:": [
                {"原始文本": test_text},
                # {"切割後句子": sentences_text},
                # {"過濾後": filtereds_text},
                {"語義分類和回饋率提取結果": uniques},
            ]
        }
        results.append(result)
        print(
            f"=========={index} Done! ====<-{(time.time() - index_start_time):.3f}->===="
        )

    total_time = time.time() - total_start_time
    results.append(
        [
            f"總共載入ㄌ {len(test_cases)} 張卡片",
            f"總測試時間: {time.strftime('%H:%M:%S', time.gmtime(total_time))}",
            f"平均時間 {(total_time / len(test_cases)):.3f} 秒/張",
        ]
    )
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(
        f"\n總共載入ㄌ {len(test_cases)} 張卡片\n總測試時間: {time.strftime('%H:%M:%S', time.gmtime(total_time))}\n平均時間 {(total_time / len(test_cases)):.3f} 秒/張\nDone!"
    )


if __name__ == "__main__":
    test_processors_11()
