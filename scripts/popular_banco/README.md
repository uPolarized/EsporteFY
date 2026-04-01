# Popular Banco de Dados

Esta pasta concentra os scripts de populacao inicial do banco usados pelo projeto.

## Comando unico (recomendado)

```bash
python manage.py popular_banco
```

Esse comando executa, em ordem:
1. `seed_esporte`
2. `seed_quadras`
3. Criacao/atualizacao do superusuario padrao (`jao` / `123`)
4. Configuracao do SocialApp Google
5. Seed de partidas demo (quando possivel)

## Opcoes

Rodar sem criar partidas demo:

```bash
python manage.py popular_banco --sem-partidas
```

Definir outro organizador para seed de partidas:

```bash
python manage.py popular_banco --organizador SeuUsuario
```

## Compatibilidade

Os scripts legados na raiz (`create_user.py`, `setup_social_apps.py`, `seed_partidas_joaovictorzz.py`) continuam funcionando como wrappers para estes modulos.
