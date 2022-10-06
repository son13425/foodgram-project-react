import webcolors
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from ingredients.models import Ingredients
from recipes.models import (FavoriteRecipes, IngredientInRecipe, Recipe,
                            ShoppingList)
from rest_framework import serializers
from tags.models import Tag
from users.models import Follow, User


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError(
                'Для этого цвета нет имени'
            )
        return webcolors.hex_to_name(data)


class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name'
        )


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(
        label='Подписан ли текущий пользователь на этого'
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request').user.id
        return Follow.objects.filter(
            user=request,
            author=obj.id
        ).exists()


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    following = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username',
    )

    class Meta:
        model = Follow
        fields = (
            'id',
            'user',
            'author'
        )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'following'],
                message='Повторная подписка запрещена'
            )
        ]

    def validate_following(self, obj):
        request = self.context.get('request')
        if request.user == obj:
            raise serializers.ValidationError(
                'Подписка на себя запрещена'
            )
        return obj


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=IngredientInRecipe.objects.all(),
                fields=['ingredient', 'recipe'],
                message='Этот продукт уже добавлен в рецепт'
            )
        ]


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(
        read_only=True
    )
    tags = TagSerializer(many=True, read_only=False)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipe_amount',
        read_only=False
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(
        label='Находится ли в избранном'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        label='Находится ли в корзине'
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'text',
            'author',
            'image',
            'ingredients',
            'tags',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def in_card(self, obj, model):
        request = self.context.get('request').user.id
        return model.objects.filter(
            user=request,
            recipe=obj.id
        ).exists()

    def get_is_favorited(self, obj):
        return self.in_card(obj, FavoriteRecipes)

    def get_is_in_shopping_cart(self, obj):
        return self.in_card(obj, ShoppingList)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeCreateSerializer()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'name',
            'text',
            'image',
            'ingredients',
            'tags',
            'cooking_time'
        )

    def ingredients_amount(self, ingredients, recipe):
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient = int(ingredient['id'])
            ingredients = IngredientInRecipe.objects.get_or_create(
                recipe=recipe,
                ingredients=ingredient,
                amount=amount
            )

    @transaction.atomic
    def create(self, validated_data):
        image = validated_data.pop('image')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        recipe.tags.set(tags)
        recipe.ingredients.set(ingredients)
        recipe.save()
        self.ingredients_amount(ingredients, recipe)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        IngredientInRecipe.objects.filter(recipe=recipe).delete()
        self.ingredients_amount(ingredients, recipe)
        recipe.tags.set(tags)
        return super().update(recipe, validated_data)

    def to_representation(self, recipe):
        return RecipeSerializer(
            recipe,
            context={'request': self.context.get('request')}
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class UserWithRecipesSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField(
        label='Подписан ли текущий пользователь на этого'
    )
    recipes = serializers.SerializerMethodField(
        label='Рецепты пользователя'
    )
    recipes_count = serializers.SerializerMethodField(
        label='Общее количество рецептов пользователя'
    )

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request').user
        return Follow.objects.filter(
            user=request,
            author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request').user.id
        limit = request.Get.get('recipes_limit')
        queryset = Recipe.objects.filter(
            author=obj.author
        )
        if limit is not None:
            queryset = Recipe.objects.filter(
                author=obj.author
            )[:int(limit)]
        return RecipeMinifiedSerializer(
            queryset,
            many=True
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(
            author=obj.author
        ).count()


class FavoriteRecipesSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = FavoriteRecipes
        fields = (
            'id',
            'user',
            'recipe',
        )

    def validate(self, data):
        request = self.context.get('request')
        recipe_id = data['recipe'].id
        favorite_exists = FavoriteRecipes.objects.filter(
            user=request.user,
            recipe__id=recipe_id
        ).exists()
        if favorite_exists:
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeMinifiedSerializer(
            instance.recipe,
            context=context
        ).data


class ShoppingListSerializer(FavoriteRecipesSerializer):
    class Meta(FavoriteRecipesSerializer.Meta):
        model = ShoppingList
        fields = (
            'id',
            'user',
            'recipe',
        )

    def validate(self, data):
        request = self.context.get('request')
        recipe_id = data['recipe'].id
        shopping_list_exists = ShoppingList.objects.filter(
            user=request.user,
            recipe__id=recipe_id
        ).exists()
        if shopping_list_exists:
            raise serializers.ValidationError(
                'Рецепт уже есть в списке покупок'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeMinifiedSerializer(
            instance.recipe,
            context=context).data
