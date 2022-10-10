import webcolors
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from ingredients.models import Ingredients
from recipes.models import (FavoriteRecipes, IngredientInRecipe, Recipe,
                            ShoppingList, TagsRecipe)
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


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

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


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(
        read_only=True
    )
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipe_amount',
        read_only=False
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()
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
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipe_amount',
        read_only=False
    )
    tags = TagSerializer(many=True)
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

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        tags_list = []
        for tag in tags:
            current_tag = TagsRecipe.objects.create(
                tag=tag,
                recipe=recipe
            )
            tags_list.append(current_tag)
        TagsRecipe.objects.bulk_create(tags_list)
        ingredients_list = []
        for ingredient in ingredients:
            current_ingredient = IngredientInRecipe.objects.create(
                ingredient=Ingredients.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount'],
            )
            ingredients_list.append(current_ingredient)
        IngredientInRecipe.objects.bulk_create(ingredients_list)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        tags_data = validated_data.pop('tags')
        tags_list = []
        for tag in tags_data:
            current_tag = TagsRecipe.objects.create(
                tag=tag,
                recipe=instance
            )
            tags_list.append(current_tag)
        instance.tags.set(tags_list)
        ingredients_data = validated_data.pop('ingredients')
        ingredients_list = []
        for ingredient in ingredients_data:
            current_ingredient = IngredientInRecipe.objects.create(
                ingredient=Ingredients.objects.get(id=ingredient['id']),
                recipe=instance,
                amount=ingredient['amount'],
            )
            ingredients_list.append(current_ingredient)
        instance.ingredients.set(ingredients_list)
        instance.save()
        return instance

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
