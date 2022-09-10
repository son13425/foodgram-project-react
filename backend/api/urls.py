from django.urls import include, path
from rest_framework.routers import DefaultRouter

from backend.ingredients.models import Ingredients

from .views import (TagViewSet,
                    UserViewSet,
                    IngredientsViewSet,
                    RecipesViewSet)


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientsViewSet)
router.register(r'recipes', RecipesViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', include('djoser.urls.jwt')),
]
