import resource
import asyncio
import aiohttp
import aioredis

from unidecode import unidecode
from bs4 import BeautifulSoup


domains = [
    'https://memgraph.com',
    'https://docs.memgraph.com',
]


def is_base_domain(url: str) -> bool:
    """Returs `True` if the url is a part of any base domain.
    `False` otherwise.
    """
    return any(url.startswith(domain) for domain in domains)


async def scrape(redis: aioredis.commands.Redis) -> None:
    """Pops an url to scrape from the `stream` and writes the text
    to `words.txt`.
    """
    try:
        base_url = await redis.blpop('stream', encoding='utf-8')[1]
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, timeout=5) as response:
                text = await asyncio.wait_for(response.text(), 5)
                soup = BeautifulSoup(text, 'html.parser')
    except Exception:
        return

    tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']
    text = ' '.join(tag.text for tag in soup.find_all(tags))
    if await redis.sismember('hashes', hash(text)):
        return

    await redis.sadd('hashes', hash(text))
    with open('words.txt', 'a+') as f:
        print(unidecode(text, errors='ignore'), file=f)

    for link in soup.find_all('a', href=True):
        url = link['href'].split('?', 1)[0].split('#', 1)[0].rstrip('/')

        if not url or url.startswith('/'):
            url = base_url + url

        if is_base_domain(url) and not await redis.sismember('seen', url):
            await redis.sadd('seen', url)
            await redis.lpush('stream', url)


async def main(max_calls: int) -> None:
    """Scrapes all text from urls on `domains` and writes it to `words.txt`.
    Runs until the `stream` queue in redis is empty.
    Creates `n` workers where `n` is the smaller of `max_calls` and the
    length of `stream`.
    `stream` is a task queue (redis list).
    `seen` holds completed tasks (redis set).
    `hashes` holds hashes of the content on an url (redis set).
    """
    redis = await aioredis.create_redis_pool('redis://localhost')

    await redis.delete('stream', 'hashes', 'seen')
    for domain in domains:
        await redis.lpush('stream', domain)

    try:
        while n := await redis.llen('stream'):
            await asyncio.gather(
                *[scrape(redis) for _ in range(min(n, max_calls))],
                return_exceptions=False,
            )
    finally:
        redis.close()
        await redis.wait_closed()


if __name__ == '__main__':
    max_open_files = resource.getrlimit(resource.RLIMIT_NOFILE)[0] // 2
    asyncio.run(main(max_calls=max_open_files))
