from django.core.validators import RegexValidator


validate_username = RegexValidator(
    r'^[\w.@+-]+\z',
    'Использованы недопустимые символы!'
)
