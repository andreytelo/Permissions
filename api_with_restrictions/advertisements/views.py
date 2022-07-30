from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from advertisements.filters import AdvertisementFilter
from advertisements.models import Advertisement, Favourite
from advertisements.permissioms import IsOwner
from advertisements.serializers import AdvertisementSerializer


class AdvertisementViewSet(ModelViewSet):
    """ViewSet для объявлений."""
    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    filterset_class = AdvertisementFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        queryset = Advertisement.objects.filter(status__in=["OPEN", "CLOSED"])
        if self.request.user.is_authenticated:
            draft = Advertisement.objects.filter(creator=self.request.user, status="DRAFT")
            return queryset | draft
        return queryset

    def get_permissions(self):
        """Получение прав для действий."""
        if self.action == "create":
            return [IsAuthenticated()]
        elif self.action in ["destroy", "update", "partial_update"]:
            return [IsAuthenticated(), IsOwner()]
        return []

    @action(detail=True, methods=['POST'], url_path=r'fav')
    def fav(self, request, pk=None):
        advertisement = self.get_object()
        advertisement_in_favourites = Favourite.objects.filter(user=self.request.user).filter(
            advertisement=advertisement.id)

        if advertisement.draft:
            raise ValidationError({'error': 'You cannot add draft to fav'})

        if advertisement_in_favourites.exists():
            raise ValidationError({'error': 'Adv already have in fav'})

        if advertisement.creator == self.request.user:
            return Response({'status': 'You cannot add your own ads'})

        advertisement.favourite.add(self.request.user)
        advertisement.save()
        return Response({'status': f'advertisement #{advertisement.id} was added in favourites'})


