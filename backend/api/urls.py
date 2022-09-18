from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (#APIUser,
                    TagViewSet,
                    IngredientsViewSet,
                    RecipesViewSet,
                    UserViewSet)


app_name = 'api'


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='tags')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'recipes', RecipesViewSet, basename='recipes')


urlpatterns = [
#   path('users/', APIUser.as_view()),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
]
