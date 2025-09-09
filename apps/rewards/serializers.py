from apps.rewards.models import RewardCategory
from apps.cards.models import CreditCard
from rest_framework import serializers


class CardSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CreditCard
        fields = ["name", "bank"]


class RewardSerializer(serializers.HyperlinkedModelSerializer):
    card = CardSerializer(read_only=True)

    class Meta:
        model = RewardCategory
        fields = ["card", "category", "scope", "min_rate", "max_rate", "reward_type"]
