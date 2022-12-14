import csv

from django.core.management.base import BaseCommand

from tags.models import Tag


class Command(BaseCommand):
    help = 'Наполнение БД тегами из файла CSV'

    def handle(self, *args, **options):
        filename = '../data/tags.csv'
        try:
            with open(
                filename,
                'r',
                encoding='UTF-8'
            ) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                next(csv_reader)
                for row in csv_reader:
                    Tag.objects.get_or_create(
                        name=row[0],
                        color=row[1],
                        slug=row[2]
                    )
        except FileNotFoundError:
            print(f'Файл {filename} не найден')
