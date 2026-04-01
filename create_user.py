import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esportefy.settings')

import django

django.setup()

from scripts.popular_banco.criar_superusuario_padrao import run


if __name__ == '__main__':
    result = run()
    if result['created']:
        print(f"✓ Superusuario '{result['username']}' criado com sucesso!")
    else:
        print(f"✓ Superusuario '{result['username']}' atualizado!")

    print(f"  Username: {result['username']}")
    print(f"  Senha: {result['password']}")
    print(f"  Email: {result['email']}")
