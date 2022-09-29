import csv

from django.core.management.base import BaseCommand
from ingredients.models import Ingredients


class Command(BaseCommand):
    help = 'Наполнение БД из файла CSV'

    def handle(self, *args, **options):
        filename = '../data/ingredients.csv'
        try:
            with open(
                filename,
                'r',
                encoding='UTF-8'
            ) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                next(csv_reader)
                for row in csv_reader:
                    Ingredients.objects.get_or_create(
                        name=row[0],
                        measurement_unit=row[1]
                    )
        except FileNotFoundError:
            print(f'Файл {filename} не найден')
