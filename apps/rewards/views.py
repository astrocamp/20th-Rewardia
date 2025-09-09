# Create your views here.
from rest_framework import viewsets
from .serializers import RewardSerializer
from .models import RewardCategory


class RewardViewSet(viewsets.ModelViewSet):
    queryset = RewardCategory.objects.all().order_by("-max-rate")
    serializer_class = RewardSerializer
