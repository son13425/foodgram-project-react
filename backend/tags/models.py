from django.db import models
from users.validators import validate_hex_color


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        verbose_name='Название',
        help_text='Название'
    )
    color = models.CharField(
        default='#FF0000',
        max_length=7,
        unique=True,
        validators=[validate_hex_color],
        verbose_name='Цвет в HEX',
        help_text='Цвет в HEX'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Уникальный слаг',
        help_text='Уникальный слаг'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name
