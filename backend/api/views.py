from http import HTTPStatus
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from ingredients.models import Ingredients
from recipes.models import FavoriteRecipes, Recipe, ShoppingList
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from tags.models import Tag
from users.models import Follow, User

from .filters import IngredientNameFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import AuthorOrReadOnly, AdminOrReadOnly
from .serializers import (FollowSerializer, IngredientsSerializer,
                          RecipeCreateUpdateSerializer, RecipeSerializer,
                          TagSerializer, UserCreateSerializer, UserSerializer,
                          UserWithRecipesSerializer, RecipeMinifiedSerializer)
from .services import get_ingredients_for_shopping


class IngredientsViewSet(viewsets.ModelViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filterset_class = IngredientNameFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def __add_recipe(model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(recipe=recipe, user=request.user)
        serializer = RecipeMinifiedSerializer(recipe)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    @staticmethod
    def __delete_recipe(model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.filter(recipe=recipe, user=request.user).delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.__add_recipe(FavoriteRecipes, request, pk)
        return self.__delete_recipe(FavoriteRecipes, request, pk)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def recipe(self, request, pk):
        if request.method == 'POST':
            return self.__add_recipe(Recipe, request, pk)
        return self.__delete_recipe(Recipe, request, pk)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.__add_recipe(ShoppingList, request, pk)
        return self.__delete_recipe(ShoppingList, request, pk)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        return get_ingredients_for_shopping(user)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPagination
    serializer_class = UserSerializer
    search_fields = ('username', 'email')
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = UserWithRecipesSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated]
    ) 
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            serializer = FollowSerializer(
                Follow.objects.create(
                    user=request.user,
                    author=author
                ),
                context={'request': request},
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        Follow.objects.filter(
            user=request.user,
            author=author
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
