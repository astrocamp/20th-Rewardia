# Create your views here.
from rest_framework.response import Response
from apps.ext_api.serializers import RewardSerializer
from apps.rewards.models import RewardCategory
from rest_framework.decorators import api_view
from django.db.models.functions import Coalesce


@api_view(["GET"])
def get_rewards(request):
    all_rewards = RewardCategory.objects.filter(is_active=True).order_by("-max_rate")
    serializer = RewardSerializer(all_rewards, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_category_rewards(request, category):
    reward_category = RewardCategory.objects.filter(
        category=category, is_active=True
    ).order_by("-max_rate")
    serializer = RewardSerializer(reward_category, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_merchant_rewards(request, scope):
    reward_merchant = RewardCategory.objects.filter(
        scope=scope,
        is_active=True,
    ).order_by(Coalesce("max_rate", "min_rate", 0).desc())
    serializer = RewardSerializer(reward_merchant, many=True)
    return Response(serializer.data)
