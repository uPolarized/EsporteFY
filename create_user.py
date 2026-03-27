import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esportefy.settings')
import django
django.setup()

from django.contrib.auth.models import User

# Criar ou atualizar usuário
user, created = User.objects.get_or_create(
    username='jao',
    defaults={
        'email': 'jao@teste.com',
        'is_superuser': True,
        'is_staff': True,
    }
)

user.set_password('123')
user.save()

if created:
    print("✓ Superusuário 'jao' criado com sucesso!")
else:
    print("✓ Superusuário 'jao' atualizado!")

print(f"  Username: jao")
print(f"  Senha: 123")
print(f"  Email: {user.email}")
