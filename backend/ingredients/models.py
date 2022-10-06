from django.db import models


class Ingredients(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text='Название'
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения',
        help_text='Единица измерения'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.id}'
