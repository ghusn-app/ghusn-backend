from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from dotenv import load_dotenv


sys.path.append(os.getcwd())  # عشان يلاقي مجلد app

load_dotenv()

from app.database import Base
from app.models.user import User
from app.models.admin import Admin
from app.models.farmer import Farmer
from app.models.diagnosis import Diagnosis
from app.models.diseases import Diseases
from app.models.payments import Payment
from app.models.refresh_token import RefreshToken
from app.models.plant import Plant

# 3. جلب كائن إعدادات Alembic
config = context.config

# 4. جلب رابط قاعدة البيانات ديناميكياً من .env وتجاوز القيمة الموجودة في alembic.ini
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
# 5. إعداد نظام الـ Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 6. تعيين المخطط الهيكلي للجداول (السطر الأساسي للـ autogenerate)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """تشغيل الهجرات في وضع الأوفلاين (بدون اتّصال مباشر)"""
    config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))  # ← السطر المضاف
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """تشغيل الهجرات في وضع الأونلاين (الاتصال المباشر بقاعدة البيانات)"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()