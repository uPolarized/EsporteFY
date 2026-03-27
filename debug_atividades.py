from social.models import Atividade
from django.contrib.auth.models import User

joao = User.objects.get(username='joao_victor')
atividades = Atividade.objects.filter(ator=joao).order_by('-timestamp')[:10]

print('\n=== DEBUG ATIVIDADES (CORRIGIDO) ===\n')
for a in atividades:
    obj = a.get_objeto()
    titulo = getattr(obj, 'titulo', None) if obj else None
    desc = a.get_descricao_formatada()
    print(f'ID={a.id}')
    print(f'  verbo: {repr(a.verbo)}')
    print(f'  obj: {obj} (id={obj.id if obj else None})')
    print(f'  titulo: {titulo}')
    print(f'  descricao_formatada: {desc}')
    print()
