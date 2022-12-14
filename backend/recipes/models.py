from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.constraints import UniqueConstraint

from ingredients.models import Ingredients
from tags.models import Tag
from users.models import User


class Recipe(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Название',
        help_text='Название'
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Описание'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author_recipe',
        verbose_name='Автор рецепта',
        help_text='Автор рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение',
        help_text='Изображение'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        verbose_name='Ингредиенты',
        through='IngredientInRecipe'
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagsRecipe',
        verbose_name='Теги',
        help_text='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            1,
            message='Минимальное время приготовления - 1 минута'
        )],
        verbose_name='Время приготовления (в минутах)',
        help_text='Время приготовления (в минутах)'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        help_text='Дата публикации'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name', 'author'],
                name='unique_name_author'
            )
        ]
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}'


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_amount',
        verbose_name='Рецепт',
        help_text='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Ингредиент в рецепте',
        help_text='Ингредиент в рецепте'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            1,
            message='Минимальное количество ингредиента - 1'
        )],
        verbose_name='Количество ингридиента в рецепте',
        help_text='Количество ингридиента в рецепте'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient'
            )
        ]
        ordering = ['-ingredient', ]
        verbose_name = 'Количество ингридиента в рецепте'
        verbose_name_plural = 'Количество ингридиентов в рецепте'

    def __str__(self):
        return (f'{self.ingredient.name} - '
                f'{self.amount} {self.ingredient.measurement_unit}')


class TagsRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тэг рецепта',
        help_text='Тэг рецепта')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_tag',
        verbose_name='Рецепт',
        help_text='Рецепт'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'tag'],
                name='unique_tag'
            )
        ]
        ordering = ['-tag', ]
        verbose_name = 'Тег в рецепте'
        verbose_name_plural = 'Теги в рецепте'

    def __str__(self):
        return f'{self.tag}'


class FavoriteRecipes(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_favorites',
        verbose_name='Автор списка избранного',
        help_text='Автор списка избранного'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_favorites',
        verbose_name='Рецепт из списка избранного',
        help_text='Рецепт из списка избранного'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipes'
            )
        ]
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном у {self.user}'


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_shoppinglist',
        verbose_name='Автор списка покупок',
        help_text='Автор списка покупок'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_shoppinglist',
        verbose_name='Список покупок',
        help_text='Список покупок'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppinglist_recipe'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'Рецепт {self.recipe} в списке покупок у {self.user}'
