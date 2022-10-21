import webcolors
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from ingredients.models import Ingredients
from recipes.models import (FavoriteRecipes, IngredientInRecipe, Recipe,
                            ShoppingList, TagsRecipe)
from tags.models import Tag
from users.models import Follow, User


class Hex2NameColor(serializers.Field):
    """Пользовательское поле для HEX-цвета"""
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
    """Создание юзера"""
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
    """Управление юзером"""
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
        user = self.context['request']
        if user is None or user.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=user.user, author=obj
        ).exists()


class FollowSerializer(serializers.ModelSerializer):
    """Подписка на юзера"""
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
            'user',
            'following'
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
    """Отображение тэгов"""
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )


class TagRecipeCreateSerializer(serializers.ModelSerializer):
    """Присвоение тэгов рецепту"""
    class Meta:
        model = TagsRecipe
        fields = (
            'tag',
            'recipe'
        )


class IngredientsSerializer(serializers.ModelSerializer):
    """Ингредиенты"""
    class Meta:
        model = Ingredients
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Отображение ингредиентов в рецепте"""
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


class CreateIngredientInRecipeSerializer(serializers.ModelSerializer):
    """Добавление ингредиентов в рецепт"""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'amount'
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Вывод рецептов"""
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
    """Создание и редактирование рецепта"""
    ingredients = CreateIngredientInRecipeSerializer(
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
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
            'cooking_time',
            'author'
        )
        read_only_fields = ('author',)

    def validate(self, data):
        tags = data['tags']
        if tags is None:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один тэг'
            )
        cooking_time = data['cooking_time']
        if int(cooking_time) <= 0:
            raise serializers.ValidationError(
                'Минимальное время приготовления - 1 минута'
            )
        ingredients = data['ingredients']
        if ingredients is None:
            raise serializers.ValidationError(
                'Вы забыли добавить ингредиенты'
            )
        ingredients_list = []
        for ingredient in ingredients:
            name = ingredient['id']
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    f'Минимальное количество {name} - 1'
                )
            if name in ingredients_list:
                raise serializers.ValidationError(
                    f'Ингредиент {name} уже добавлен'
                )
            ingredients_list.append(name)
        return data

    def add_tag(self, tags, recipe):
        tag_list = []
        for tag in tags:
            current_tag = TagsRecipe(
                tag=tag,
                recipe=recipe
            )
            tag_list.append(current_tag)
        TagsRecipe.objects.bulk_create(tag_list)

    def add_ingredient(self, ingredients, recipe):
        ingredient_list = []
        for ingredient in ingredients:
            current_ingredient = IngredientInRecipe(
                ingredient=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            )
            ingredient_list.append(current_ingredient)
        IngredientInRecipe.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        image = validated_data.pop('image')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        self.add_tag(tags, recipe)
        self.add_ingredient(ingredients, recipe)
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
        instance.tags.clear()
        self.add_tag(tags_data, instance)
        ingredients_data = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.add_ingredient(ingredients_data, instance)
        instance.save()
        return instance

    def to_representation(self, recipe):
        return RecipeSerializer(
            recipe,
            context={'request': self.context.get('request')}
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Мини-формат рецепта"""
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class UserWithRecipesSerializer(serializers.ModelSerializer):
    """Автор с рецептами"""
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
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=obj.user,
            author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if limit is not None:
            queryset = Recipe.objects.filter(
                author=obj.author
            )[:int(limit)]
        return RecipeMinifiedSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(
            author=obj.author
        ).count()
