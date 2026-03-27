#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esportefy.settings')
django.setup()

from django.contrib.auth.models import User
from perfis.models import SolicitacaoAmizade

# Pegar usuários
users = User.objects.all()
if len(users) >= 2:
    u1 = users[0]
    u2 = users[1]
    print(f"✅ Usuários encontrados: {u1.username}, {u2.username}")
    
    # Criar solicitação se não existir
    sol, created = SolicitacaoAmizade.objects.get_or_create(
        solicitante=u1, 
        receptor=u2
    )
    if created:
        print(f"✅ Nova solicitação criada!")
    else:
        print(f"✅ Solicitação já existe")
    
    # Testar a API
    print("\n✅ Testando API...")
    recebidas = SolicitacaoAmizade.objects.filter(receptor=u2)
    enviadas = SolicitacaoAmizade.objects.filter(solicitante=u1)
    
    print(f"📬 Recebidas por {u2.username}: {recebidas.count()}")
    print(f"📤 Enviadas por {u1.username}: {enviadas.count()}")
    
else:
    print("⚠️  Menos de 2 usuários no banco")
