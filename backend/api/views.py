from django.shortcuts import render
from rest_framework import viewsets

from .serializers import (IngredientsSerializer,
                        IngredientInRecipeSerializer,
                        FavoriteRecipesSerializer,
                        FollowSerializer,
                        RecipeSerializer,
                        ShoppingListSerializer,
                        TagSerializer,
                        UserSerializer)
from ingredients.models import Ingredients
from recipes.models import (Recipe,
                            IngredientInRecipe,
                            FavoriteRecipes,
                            ShoppingList)
from tags.models import Tag
from users.models import Follow, User


class IngredientsViewSet(viewsets.ModelViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer


class IngredientInRecipeViewSet(viewsets.ModelViewSet):
    queryset = IngredientInRecipe.objects.all()
    serializer_class = IngredientInRecipeSerializer


class FavoriteRecipesViewSet(viewsets.ModelViewSet):
    queryset = FavoriteRecipes.objects.all()
    serializer_class = FavoriteRecipesSerializer


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer


class ShoppingListViewSet(viewsets.ModelViewSet):
    queryset = ShoppingList.objects.all()
    serializer_class = ShoppingListSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
