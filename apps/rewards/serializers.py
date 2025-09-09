from models import RewardCategory
from rest_framework import serializers


class RewardSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RewardCategory
        fields = ["card", "nlp_scope", "min_rate", "max_rate", "reward_type"]
