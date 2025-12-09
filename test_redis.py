import asyncio
import redis.asyncio as redis

async def test_redis():
    try:
        print("Tentando conectar ao Redis...")
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        await r.set("chave_teste", "valor_teste")
        valor = await r.get("chave_teste")
        print("Valor recuperado do Redis:", valor)
        await r.close()
    except Exception as e:
        print("Erro:", e)

if __name__ == "__main__":
    asyncio.run(test_redis())
