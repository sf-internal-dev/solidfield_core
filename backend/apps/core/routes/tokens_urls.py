from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.urls import path

urlpatterns = [
    path('tokenjwt/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('tokenjwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]