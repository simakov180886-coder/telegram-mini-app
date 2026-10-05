import os, json
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.types import LabeledPrice, PreCheckoutQuery

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change_me")
BASE_URL = os.getenv("BASE_URL", "")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/create-invoice")
async def create_invoice(request: Request):
    data = await request.json()
    stars = int(data.get("stars", 10))
    coins = int(data.get("coins", 500))
    user_id = int(data.get("user_id", 0))
    link = await bot.create_invoice_link(
        title=f"{coins} игровых монет",
        description=f"Покупка {coins} монет за {stars} Stars",
        payload=json.dumps({"user_id": user_id, "coins": coins}),
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{coins} монет", amount=stars)],
    )
    return {"invoice_link": link}

@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message()
async def on_message(message: types.Message):
    if message.successful_payment:
        payload = json.loads(message.successful_payment.invoice_payload)
        coins = payload["coins"]
        user_id = payload["user_id"]
        print(f"User {user_id} paid, +{coins} coins")
        await message.answer(f"✅ Зачислено {coins} монет!")

@app.post("/webhook")
async def webhook(request: Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != WEBHOOK_SECRET:
        return {"ok": False}, 403
    update = types.Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    if BASE_URL and BOT_TOKEN:
        await bot.set_webhook(
            url=f"{BASE_URL}/webhook",
            secret_token=WEBHOOK_SECRET,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
        print(f"Webhook set to {BASE_URL}/webhook")

@app.get("/")
async def root():
    return {"status": "ok", "service": "kyrgyz-casino-bot"}
