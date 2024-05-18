"""
Django command to wait for db to be available
"""

import time

from psycopg2 import OperationalError as Psycopy2Error
from django.db.utils import OperationalError
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write("Waiting for db...")
        is_db_up = False

        while not is_db_up:
            try:
                self.check(databases=["default"])
                is_db_up = True
            except (OperationalError, Psycopy2Error):
                self.stdout.write("DB not available yet")
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS("DB available"))
