from django.db.models import QuerySet
from rest_framework import generics

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


class NotificationCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)


class NotificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self) -> QuerySet[Notification]:
        return Notification.objects.filter(
            recipient=self.request.user,
        ).select_related("comment", "comment__author", "comment__post")


class NotificationReadAllView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def post(self, request, *args, **kwargs):
        updated_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)

        return Response(
            {"marked_as_read": updated_count}, status=status.HTTP_200_OK
        )
