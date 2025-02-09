import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import asyncio

#from keep_alive import keep_alive
#keep_alive()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

# Zmienne globalne do przechowywania ustawień użytkownika
price_min = None
price_max = None
sleep_time = None
phone_name = ''
visited_links = set()
auto_open = False
monitor = None  # Zmienna globalna dla pętli monitorującej
def reset_global_variables():
    global price_min, price_max, sleep_time, phone_name
    price_min = None
    price_max = None
    sleep_time = None
    phone_name = ''


@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} jest gotowy!')

# Komenda do ustawienia minimalnej ceny
@bot.command()
async def min(ctx, value: int):
    global price_min
    price_min = value
    await ctx.send(f"Minimalna cena ustawiona na: {price_min} zł")

# Komenda do ustawienia maksymalnej ceny
@bot.command()
async def max(ctx, value: int):
    global price_max
    price_max = value
    await ctx.send(f"Maksymalna cena ustawiona na: {price_max} zł")

# Komenda do ustawienia czasu odświeżania
@bot.command()
async def s(ctx, value: int):
    global sleep_time
    sleep_time = value
    await ctx.send(f"Czas odświeżania ustawiony na: {sleep_time} sekund")

# Komenda do ustawienia nazwy telefonu
@bot.command()
async def ip(ctx, value: str = ''):
    global phone_name
    phone_name = value
    await ctx.send(f"Nazwa telefonu ustawiona na: {phone_name}")

@bot.command()
async def start(ctx):
    await ctx.send("Monitorowanie rozpoczęte!")
    #channel_id = 1305482509622054923
    #channel = bot.get_channel(channel_id)
    #await channel.send("Rozpoczynam monitorowanie")
    global price_min, price_max, sleep_time, phone_name, visited_links, auto_open, monitor

    # Sprawdzenie, czy wszystkie parametry zostały ustawione
    if price_min is None or price_max is None or sleep_time is None:
        await ctx.send("Ustaw wszystkie parametry przed rozpoczęciem: .min, .max, .s, .ip")
        return

    if price_min > price_max:
        await ctx.send("Minimalna cena nie może być większa od maksymalnej.")
        return

    auto_open = True
    visited_links = set()

    sort_by = 'created_at:desc'
    url = (
        f'https://www.olx.pl/elektronika/telefony/smartfony-telefony-komorkowe/iphone/'
        f'?search%5Border%5D={sort_by}&search%5Bfilter_float_price:from%5D={price_min}&search%5Bfilter_float_price:to%5D={price_max}'
    )
    if phone_name:
        url += f'&search%5Bfilter_enum_phonemodel%5D%5B0%5D={phone_name}'

    @tasks.loop(seconds=sleep_time)
    async def monitor():
        global visited_links
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        table = soup.find('div', class_='css-j0t2x2')
        if not table:
            await ctx.send("Nie znaleziono danych na stronie.")
            return

        itemName = table.find_all('h6', class_='css-1wxaaza')
        price = table.find_all('p', class_='css-13afqrm')
        links = table.find_all('a', class_='css-z3gu2d')
        hrefs = list(dict.fromkeys(link['href'] for link in links))

        if itemName and price and hrefs:
            currentFirstItem = f"{itemName[3].text}:{price[3].text}"
            current_link = f"https://www.olx.pl{hrefs[3]}"

            if current_link not in visited_links:
                visited_links.add(current_link)
                message = f"{itemName[3].text}\nCENA: {price[3].text}\nLINK: {current_link}"
                await ctx.send(message)

    monitor.start()
    #await ctx.send("Monitorowanie rozpoczęte!")
@bot.command()
async def stop(ctx):
    global monitor
    if monitor is not None and monitor.is_running():
        monitor.stop()
        reset_global_variables()
        await ctx.send("Monitorowanie zatrzymane.")
    else:
        await ctx.send("Monitorowanie nie jest aktywne.")

bot.run('DISCORD_TOKEN')#main
