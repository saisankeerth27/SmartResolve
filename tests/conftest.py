import sys
sys.path.insert(0, '.')

from src.database.db import init_database
from src.core.config import DATABASE_PATH

init_database(DATABASE_PATH)
