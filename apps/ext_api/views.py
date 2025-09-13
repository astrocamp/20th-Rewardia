# Create your views here.
from rest_framework.response import Response
from apps.ext_api.serializers import RewardSerializer, UserCardSerializer
from apps.rewards.models import RewardCategory
from apps.users.models import UserCard
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from django.db.models.functions import Coalesce
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated


@api_view(["GET"])
def get_rewards(request):
    all_rewards = (
        RewardCategory.objects.select_related("card")
        .filter(is_active=True)
        .order_by("-max_rate")
    )
    serializer = RewardSerializer(all_rewards, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_category_rewards(request, category):
    reward_category = (
        RewardCategory.objects.select_related("card")
        .filter(category=category, is_active=True)
        .order_by("-max_rate")
    )
    serializer = RewardSerializer(reward_category, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_merchant_rewards(request, scope):
    reward_merchant = (
        UserCard.objects.select_related("card")
        .filter(scope=scope, is_active=True, card__is_active=True)
        .annotate(rate=Coalesce("max_rate", "min_rate"))
        .order_by("-rate")[:10]
    )
    serializer = RewardSerializer(reward_merchant, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_user_cards(request):
    user_cards = UserCard.objects.filter(user=request.user).order_by("-added_date")
    serializer = UserCardSerializer(user_cards, many=True)
    return Response(serializer.data)
