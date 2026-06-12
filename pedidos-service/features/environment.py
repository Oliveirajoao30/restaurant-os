"""Configuração do behave: inicializa o Django e isola cada cenário em uma transação."""

import os
import sys

import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test.runner import DiscoverRunner
from django.test.utils import setup_test_environment, teardown_test_environment


def before_all(context):
    context.django_runner = DiscoverRunner()
    context.old_db_config = context.django_runner.setup_databases()
    setup_test_environment()


def after_all(context):
    teardown_test_environment()
    context.django_runner.teardown_databases(context.old_db_config)


def before_scenario(context, scenario):
    from django.db import transaction

    context.atomic = transaction.atomic()
    context.atomic.__enter__()


def after_scenario(context, scenario):
    from django.db import transaction

    transaction.set_rollback(True)
    context.atomic.__exit__(None, None, None)
