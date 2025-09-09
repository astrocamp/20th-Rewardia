# Create your views here.
from rest_framework import viewsets
from apps.rewards.serializers import RewardSerializer
from apps.rewards.models import RewardCategory


class RewardViewSet(viewsets.ModelViewSet):
    queryset = RewardCategory.objects.all().order_by("-max_rate")
    serializer_class = RewardSerializer
