from django.contrib import admin

from .models import FavoriteRecipes, IngredientInRecipe, Recipe, ShoppingList


class IngredientsInRecipeInline(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'ingredient',
        'amount',
    )
    search_fields = ('recipe__name',)
    list_filter = ('recipe',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientsInRecipeInline,)
    list_display = (
        'name',
        'text',
        'author',
        'image',
        'cooking_time',
        'pub_date',
        #'count_favorites'
    )
    search_fields = ('name', 'text', 'author',)
    list_filter = ('pub_date', 'name', 'author',)
    empty_value_display = '-пусто-'

    #def count_favorites(self, obj):
    #    return obj.favorites.count()


class FavoriteRecipesAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    empty_value_display = '-пусто-'


class ShoppingListAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    search_fields = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    empty_value_display = '-пусто-'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientInRecipe, IngredientInRecipeAdmin)
admin.site.register(FavoriteRecipes, FavoriteRecipesAdmin)
admin.site.register(ShoppingList, ShoppingListAdmin)
