# core/management/commands/say_hello.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write("Hello from custom command!")
