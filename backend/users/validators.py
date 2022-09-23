from django.core.validators import RegexValidator


validate_username = RegexValidator(
    r'^[\w.@+-]+$',
    'Использованы недопустимые символы!'
)

validate_hex_color = RegexValidator(
    r'^#([A-Fa-f0-9]{6})$',
    'Введите цвет в НЕХ-формате!'
)
