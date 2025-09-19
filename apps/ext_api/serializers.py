from apps.rewards.models import RewardCategory
from apps.cards.models import CreditCard
from apps.users.models import UserCard
from rest_framework import serializers


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = ["id", "name", "bank", "image"]


class RewardSerializer(serializers.HyperlinkedModelSerializer):
    card = CardSerializer(read_only=True)

    class Meta:
        model = RewardCategory
        fields = ["card", "category", "scope", "min_rate", "max_rate", "reward_type"]


class MinRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardCategory
        fields = ["category", "scope", "min_rate", "max_rate", "reward_type"]


class UserCardSerializer(serializers.ModelSerializer):
    card = CardSerializer(read_only=True)
    rewards = serializers.SerializerMethodField()
    # partial_card_num = serializers.SerializerMethodField()

    class Meta:
        model = UserCard
        fields = ["user", "card", "rewards"]

    def get_rewards(self, obj):
        rewards = obj.card.reward_categories.all()
        return MinRewardSerializer(rewards, many=True).data

    # def get_partial_card_num():
    #     pass
