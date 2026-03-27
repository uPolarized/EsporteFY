"""
Management command: associar_fotos_quadras
Associa os arquivos já existentes em media/fotos_quadras/ aos modelos FotoQuadra,
fazendo o matching pelo nome da quadra.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from quadras.models import Quadra, FotoQuadra


# Mapping: nome da quadra (ou parte) → lista de arquivos preferidos (em ordem de prioridade)
# Só o PRIMEIRO de cada lista vira a foto principal; os demais são fotos extras.
MAPPING = [
    (10, ['ceu.jpg', 'ceu_f7AzaOH.jpg', 'ceu_IDIxgEm.jpg']),
    (12, ['arena_caxito__.jpg', 'arena_caxito___27eJv6p.jpg', 'arena_caxito___Ab808K6.jpg',
          'arena_caxito___BFTaRjY.jpg', 'arena_caxito___Df32wE2.jpg']),
    (6,  ['arena_flamengo.jpg', 'arena_flamengo_b2isFdL.jpg', 'arena_flamengo_PYdjZhO.jpg']),
    (11, ['arena_itaipuaçu.jpg', 'arena_itaipuaçu_Qrafbcc.jpg', 'itaipuaçu.jpg']),
    (7,  ['arena_itapeba.jpeg', 'arena_itapeba_OY1vk7v.jpeg', 'arena_itapeba_uQB4vfC.jpeg']),
    (9,  ['arena_lutas.jpg', 'arena_luta.jpeg', 'arena_luta_CpDIYFj.jpeg']),
    (8,  ['arena_nd7_particular_-_numero_cell_21997618824.jpg',
          'arena_nd7_particular_-_numero_cell_21997618824_6t8ZZ7T.jpg',
          'arena_nd7_particular_-_numero_cell_21997618824_PsT6rIt.jpg']),
    (14, ['campo_de_inoã_.jpg', 'campo_de_inoã__Sq2Gi7D.jpg']),
    (15, ['Campo_do_Bananal_Complexo_Esportivo_do_Bananal.jpeg',
          'campo_do_bananal.jpg', 'campo_do_bananal_6zvsv31.jpg']),
    (13, ['caju_.jpg', 'caju__lQs6Ubu.jpg', 'caju__qoHLTYs.jpg']),
    (16, ['centro_esportivo_caxito.jpg']),
    (2,  ['guaratiba_barra_de_maricá_.jpg', 'guaratiba_barra_de_maricá__Gm2A8l3.jpg']),
    (1,  ['manu_manoela_.jpg', 'manu_manoela__1.jpg']),
    (4,  ['praça_dos_gaviões.jpg', 'praça_dos_gaviões_1.jpg', 'praça_dos_gaviões_YYp7HQR.jpg']),
    (5,  ['quadra_da_70.jpg', 'quadra_da_70_14cehdw.jpg', 'quadra_da_70_5CsCRH6.jpg']),
    (3,  ['quadtra_da_25_itaipuaçu_.jpg', 'quadtra_da_25_itaipuaçu__jRD7f3l.jpg',
          'quadtra_da_25_itaipuaçu__r4gv7dh.jpg', 'quadtra_da_25_itaipuaçu__TuYRpcT.jpg']),
]

FOTOS_DIR = os.path.join(settings.MEDIA_ROOT, 'fotos_quadras')
FOTOS_RELATIVE = 'fotos_quadras'


class Command(BaseCommand):
    help = 'Associa as fotos existentes em media/fotos_quadras/ às quadras no banco de dados.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Remove todas as FotoQuadra existentes antes de associar.',
        )

    def handle(self, *args, **options):
        if options['reset']:
            deleted, _ = FotoQuadra.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'  {deleted} FotoQuadra(s) removidas.'))

        criadas = 0
        nao_encontradas = []

        for quadra_id, filenames in MAPPING:
            try:
                quadra = Quadra.objects.get(pk=quadra_id)
            except Quadra.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  Quadra ID={quadra_id} não encontrada.'))
                continue

            for filename in filenames:
                filepath = os.path.join(FOTOS_DIR, filename)
                if not os.path.isfile(filepath):
                    nao_encontradas.append(filename)
                    continue

                relative_path = f'{FOTOS_RELATIVE}/{filename}'
                already_exists = FotoQuadra.objects.filter(quadra=quadra, imagem=relative_path).exists()
                if already_exists:
                    self.stdout.write(f'  Já existe: {quadra.nome} ← {filename}')
                    continue

                FotoQuadra.objects.create(quadra=quadra, imagem=relative_path)
                criadas += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ {quadra.nome} ← {filename}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'OK: {criadas} FotoQuadra(s) criadas.'))
        if nao_encontradas:
            self.stdout.write(self.style.WARNING(f'Arquivos não encontrados: {nao_encontradas}'))
