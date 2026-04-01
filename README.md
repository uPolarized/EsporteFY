# EsporteFY

Guia rapido para rodar o projeto somente com Docker, popular o banco e criar superusuario.

## 1) Pre-requisitos

- Docker
- Docker Compose
- Git

## 2) Configurar variaveis de ambiente

O projeto usa o arquivo [.env](.env) e esta configurado para PostgreSQL via `DATABASE_URL`.

Exemplo:

```env
DATABASE_URL=postgres://esportefy_user:coloque_uma_senha_forte_aqui@db:5432/esportefy_db
```

## 3) Rodar tudo no container

Na raiz do projeto:

```bash
docker compose up --build
```

Servicos principais:

- Django (web): http://localhost:8000
- FastAPI chat: http://localhost:8080
- PostgreSQL: servico `db`
- Redis: servico `redis`

## 4) Migracoes (dentro do container)

```bash
docker compose run --rm web python manage.py migrate
```

## 5) Popular banco com esportes, quadras e partidas

Comando unico (recomendado):

```bash
docker compose run --rm web python manage.py popular_banco
```

Esse comando executa:

1. Seed de esportes (`seed_esporte`)
2. Seed de quadras (`seed_quadras`)
3. Criacao/atualizacao de superusuario padrao
4. Configuracao do SocialApp Google
5. Seed de partidas demo

Sem criar partidas demo:

```bash
docker compose run --rm web python manage.py popular_banco --sem-partidas
```

Comandos separados (opcional):

```bash
docker compose run --rm web python manage.py seed_esporte
docker compose run --rm web python manage.py seed_quadras
```

## 6) Criar superusuario generico 

Usuario generico padrao:

- username: `nome`
- email: vazio
- senha: `123`

Para criar/atualizar esse usuario:

```bash
docker compose run --rm web python create_user.py
```

## 7) Aviso importante

- O usuario acima e apenas para ambiente de desenvolvimento.
- Em ambiente real, troque username e senha para dados seus e use senha forte.

## 8) Acessar admin

Com o servidor no ar:

- Admin: http://localhost:8000/admin
- Login: `nome`
- Senha: `123`

## 9) Comandos uteis (sempre no container)

```bash
docker compose run --rm web python manage.py makemigrations
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py collectstatic --noinput
docker compose run --rm web python manage.py test
```
