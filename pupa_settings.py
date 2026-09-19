import os

from dotenv import load_dotenv

# `pupa` is a standalone CLI that never loads oak_park_app.settings, so it
# never sees .env unless we load it here ourselves.
load_dotenv()

CACHE_DIR = os.path.join(os.getcwd(), "_cache")
SCRAPED_DATA_DIR = os.path.join(os.getcwd(), "_data")

# councilmatic_core.models imports os.path.join(settings.STATIC_ROOT, ...) at
# module load time, so pupa's minimal Django app needs some value here even
# though it never serves static files.
STATIC_ROOT = "/tmp"

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgis://postgres:postgres@postgres:5432/postgres"
)

INSTALLED_APPS = (
    "django.contrib.contenttypes",
    "opencivicdata.core.apps.BaseConfig",
    "opencivicdata.legislative.apps.BaseConfig",
    "councilmatic_core",
    "pupa",
)
