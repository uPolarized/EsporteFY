# SEU_APP/management/commands/seed_quadras.py
from django.core.management.base import BaseCommand
from django.db import transaction
from ...models import Quadra

# ==============================
# Lista de quadras (vinda do usuário)
# ==============================
QUADRAS = [
    {
        "nome": "Quadra do Manu Manoela",
        "bairro": "sao_jose",
        "descricao": "Quadra do Manu Manoela - Rua do Canal.",
        "lat": -22.93876418855109,
        "lng": -42.88660644548029,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Quadra da Praça de Guaratiba",
        "bairro": "guaratiba",
        "descricao": "Quadra da Praça de Guaratiba.",
        "lat": -22.957273973089624,
        "lng": -42.79287285082279,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Quadra da 25 - Barroco",
        "bairro": "barroco",
        "descricao": "Quadra da 25 - Barroco.",
        "lat": -22.9533737484227,
        "lng": -42.98846444885395,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Quadra da Praça dos Gaviões",
        "bairro": "itaipuaçu",
        "descricao": "Quadra da Praça dos Gaviões - Itaipuaçu.",
        "lat": -22.966401976157997,
        "lng": -42.97914277431582,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Quadra da Praça da 70",
        "bairro": "itaipuaçu",
        "descricao": "Quadra da Praça da 70 - Itaipuaçu.",
        "lat": -22.969213480880953,
        "lng": -42.93875560315207,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Arena Flamengo",
        "bairro": "flamengo",
        "descricao": "Arena Flamengo.",
        "lat": -22.9091064147854,
        "lng": -42.80462618892166,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Arena Itapeba",
        "bairro": "itapeba",
        "descricao": "Arena Itapeba.",
        "lat": -22.90879632681068,
        "lng": -42.835842199122716,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Arena ND7 (particular)",
        "bairro": "itapeba",
        "descricao": "Arena ND7 (particular).",
        "lat": -22.919040605636344,
        "lng": -42.855187974317154,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Arena Lutas",
        "bairro": "inoã",
        "descricao": "Arena Lutas - Inoã.",
        "lat": -22.906517689475255,
        "lng": -42.93548963198973,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Arena CEU (Mumbuca)",
        "bairro": "mumbuca",
        "descricao": "Arena CEU - Mumbuca.",
        "lat": -22.908534585429198,
        "lng": -42.8270423549872,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Arena Itaipuaçu",
        "bairro": "itaipuaçu",
        "descricao": "Arena Itaipuaçu (quadra coberta / complexo).",
        "lat": -22.963448803306783,
        "lng": -42.991693130406375,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Arena Caxito",
        "bairro": "caxito",
        "descricao": "Arena Caxito.",
        "lat": -22.898012166117574,
        "lng": -42.822497926982834,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Campo do Caju",
        "bairro": "caju",
        "descricao": "Campo do Caju.",
        "lat": -22.923501779794684,
        "lng": -42.79388058575433,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Campo de Inoã",
        "bairro": "inoã",
        "descricao": "Campo de Inoã.",
        "lat": -22.910519188555753,
        "lng": -42.92927932264357,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Campo do Bananal (Complexo Esportivo do Bananal)",
        "bairro": "bananal",
        "descricao": "Campo do Bananal - Complexo Esportivo do Bananal.",
        "lat": -22.927572510984724,
        "lng": -42.718376731989395,
        "fonte": "lista do usuário",
    },
    {
        "nome": "Campo do Centro Esportivo Caxito",
        "bairro": "caxito",
        "descricao": "Campo do Centro Esportivo Caxito.",
        "lat": -22.896015353243083,
        "lng": -42.8272775844126,
        "fonte": "lista do usuário",
    },
   
]

class Command(BaseCommand):
    help = "Atualiza ou cria quadras sem apagar fotos existentes."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("♻️ Atualizando ou criando quadras (sem apagar fotos)..."))

        created, updated = 0, 0

        for item in QUADRAS:
            nome = item["nome"].strip()
            bairro = item["bairro"].strip().lower()
            descricao = item.get("descricao", "")
            lat = item.get("latitude") or item.get("lat")
            lng = item.get("longitude") or item.get("lng")

            obj, was_created = Quadra.objects.update_or_create(
                nome=nome,
                defaults={
                    "bairro": bairro,
                    "descricao": descricao,
                    "latitude": lat,
                    "longitude": lng,
                    "fonte": item.get("fonte", "seed automatizado"),
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Criadas: {created} | Atualizadas: {updated}"))
