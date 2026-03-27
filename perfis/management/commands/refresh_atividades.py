from django.core.management.base import BaseCommand
from social.models import Atividade


class Command(BaseCommand):
    help = 'Refresh atividades para garantir que descrições estão corretas'

    def handle(self, *args, **options):
        """
        Testa todas as atividades para garantir que get_descricao_formatada()
        funciona corretamente. Útil para debug e validação.
        """
        atividades = Atividade.objects.all().order_by('-timestamp')
        total = atividades.count()
        
        self.stdout.write(self.style.SUCCESS(f'\n📋 Verificando {total} atividades...'))
        
        com_objeto = 0
        sem_objeto = 0
        
        for a in atividades:
            obj = a.get_objeto
            desc = a.get_descricao_formatada()
            
            if obj:
                com_objeto += 1
            else:
                sem_objeto += 1
                
            # Log de debug (primeiras 20)
            if com_objeto + sem_objeto <= 20:
                status = '✅' if obj else '⚠️ '
                print(f'{status} ID={a.id} | {desc} | verbo={a.verbo} | obj={obj}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Com objeto: {com_objeto}'))
        self.stdout.write(self.style.WARNING(f'⚠️  Sem objeto: {sem_objeto}'))
        self.stdout.write(self.style.SUCCESS(f'\n✨ Refresh concluído!'))
