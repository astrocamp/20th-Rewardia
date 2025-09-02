
import os
import django
import random

# 設定 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rewardia.settings')
django.setup()

from apps.cards.models import CreditCard
from apps.rewards.models import PendingReward

def seed_data():
    """
    生成 20 筆信用卡和 20 筆待審核回饋資料。
    """
    banks = ["國泰世華", "玉山銀行", "中國信託", "台新銀行", "富邦銀行"]
    
    card_templates = [
        {"name": "CUBE卡", "network": "VISA", "type": "SIGNATURE"},
        {"name": "U Bear卡", "network": "Mastercard", "type": "TITANIUM"},
        {"name": "LINE Pay卡", "network": "JCB", "type": "PLATINUM"},
        {"name": "momo卡", "network": "Mastercard", "type": "WORLD"},
    ]

    # 確保每個銀行的 nlp_category 都不同
    nlp_categories_pool = ["電商", "交通運輸", "餐飲", "旅遊", "超市", "百貨公司", "便利商店", "加油站"]
    
    nlp_scopes = ["國內", "海外"]
    reward_types = ["CASHBACK", "POINTS"]

    cards_to_create = []
    rewards_to_create = []

    print("準備生成信用卡資料...")

    # 為了避免重複執行時產生一樣的資料，先清除舊的測試資料
    # 這裡只刪除由這個腳本可能建立的銀行資料
    CreditCard.objects.filter(bank__in=banks).delete()
    # PendingReward 會因為 ForeignKey 的 CASCADE 設定被一併刪除

    created_cards_map = {}

    for bank_name in banks:
        # 為每家銀行從卡片模板複製一份，避免後續修改影響到其他銀行
        local_card_templates = [t.copy() for t in card_templates]
        random.shuffle(local_card_templates) # 將卡片順序打亂
        
        for i in range(4):
            template = local_card_templates[i]
            card = CreditCard(
                name=template["name"],
                bank=bank_name,
                card_network=template["network"],
                card_type=template["type"],
                foreign_transaction_fee=1.5
            )
            cards_to_create.append(card)

    # 一次性建立所有信用卡
    created_cards = CreditCard.objects.bulk_create(cards_to_create)
    print(f"成功創建 {len(created_cards)} 張信用卡。")

    # 將創建的卡片存入 map 以便查找
    for card in created_cards:
        if card.bank not in created_cards_map:
            created_cards_map[card.bank] = []
        created_cards_map[card.bank].append(card)

    print("準備生成待審核回饋資料...")
    
    for bank_name, cards_in_bank in created_cards_map.items():
        # 為每家銀行選取 4 個不重複的類別
        selected_categories = random.sample(nlp_categories_pool, 4)
        
        for i, card in enumerate(cards_in_bank):
            category = selected_categories[i]
            reward = PendingReward(
                card=card,
                nlp_category=category,
                nlp_scope=random.choice(nlp_scopes),
                extracted_sentence=f"這是一筆關於 {card.bank} {card.name} 在 {category} 的測試回饋。",
                confidence=round(random.uniform(0.85, 0.99), 3),
                min_rate=round(random.uniform(1.0, 2.5), 2),
                max_rate=round(random.uniform(2.5, 5.0), 2),
                reward_type=random.choice(reward_types)
            )
            rewards_to_create.append(reward)

    # 一次性建立所有待審核回饋
    created_rewards = PendingReward.objects.bulk_create(rewards_to_create)
    print(f"成功創建 {len(created_rewards)} 筆待審核回饋。")

    print("資料生成完畢！")

if __name__ == "__main__":
    seed_data()
