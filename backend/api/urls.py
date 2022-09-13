from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (TagViewSet,
                    UserViewSet,
                    IngredientsViewSet,
                    RecipesViewSet)


app_name = 'api'


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'recipes', RecipesViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
