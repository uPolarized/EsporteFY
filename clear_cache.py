#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esportefy.settings')
django.setup()

from django.core.cache import cache
from django.views.decorators.cache import never_cache

# Limpar cache
cache.clear()
print("✓ Cache Django limpo")

# Limpar arquivos .pyc
import shutil
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        pycache_path = os.path.join(root, '__pycache__')
        try:
            shutil.rmtree(pycache_path)
            print(f"✓ Deletado: {pycache_path}")
        except:
            pass

print("✓ Tudo limpo!")
