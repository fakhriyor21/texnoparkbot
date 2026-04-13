# Guliston Yoshlar Texnoparki — Telegram bot

**aiogram 3** bilan yozilgan anketa boti: OTM tanlash, ism/familiya, telefon, muammo, 2 xonali kod, admin qabul.

## Mahalliy ishga tushirish

1. `pip install -r requirements.txt`
2. `.env.example` ni `.env` qilib nusxalang, `BOT_TOKEN` va `ADMIN_IDS` ni to‘ldiring.
3. `python bot.py`

`.env` va `texnopark.db` repoga kiritilmaydi.

---

## Heroku ga deploy (to‘liq)

Kerak: [Heroku akkaunt](https://signup.heroku.com/), [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli), `git`.

### 1. Login

```bash
heroku login
```

### 2. Ilova yaratish

Loyiha papkasida:

```bash
cd texnoparkbot
heroku create sizning-unikal-app-nomingiz
```

Bu `heroku` nomli `git remote` qo‘shadi. Tekshirish: `git remote -v`.

### 3. Config Vars (majburiy)

Dashboard: ilova → **Settings → Config Vars → Reveal Config Vars**, quyidagilarni qo‘shing:

| Kalit | Qiymat |
|--------|--------|
| `BOT_TOKEN` | @BotFather token |
| `ADMIN_IDS` | Raqam yoki `111,222` |

Yoki CLI (PowerShellda ham ishlaydi):

```bash
heroku config:set BOT_TOKEN="TOKEN_BU_YERGA" -a sizning-unikal-app-nomingiz
heroku config:set ADMIN_IDS="TELEGRAM_ID" -a sizning-unikal-app-nomingiz
```

`BOT_TOKEN` bo‘lmasa, dyno ishga tushganda `bot.py` chiqib ketadi.

### 4. Kod yuborish (deploy)

GitHub ulanish bo‘lsa va `origin` da loyiha bo‘lsa:

```bash
git push heroku main
```

Agar sizning tarmog‘ingiz `master` bo‘lsa:

```bash
git push heroku master:main
```

yoki `git branch -M main` qilib keyin `git push heroku main`.

### 5. Worker dinamosini yoqish (majburiy)

Bu bot **worker** sifatida ishlaydi:

```bash
heroku ps:scale worker=1 -a sizning-unikal-app-nomingiz
```

`web` dinamosi kerak emas. Agar avtomatik `web` bo‘lsa:

```bash
heroku ps:scale web=0 worker=1 -a sizning-unikal-app-nomingiz
```

### 6. Tekshirish

```bash
heroku logs --tail -a sizning-unikal-app-nomingiz
```

Logda `Bot ishga tushmoqda (aiogram)...` va `Start polling` ko‘rinishi kerak. Birinchi marta `Heroku muhitida ishlayapti` qatori bo‘lishi mumkin.

Telegramda botga `/start` yuboring.

---

### Muammolarni bartaraf etish

| Muammo | Nima qilish |
|--------|-------------|
| **Build: Python topilmadi** | `runtime.txt` dagi versiyani [Heroku qo‘llab-quvvatlash](https://devcenter.heroku.com/articles/python-support) bo‘yicha o‘zgartiring (masalan `python-3.12.7`). |
| **R10 Boot timeout / crash** | `heroku logs --tail` — odatda `BOT_TOKEN` yo‘q yoki noto‘g‘ri. |
| **Worker ishlamayapti** | `heroku ps` — `worker` `up` bo‘lishi kerak; `ps:scale worker=1` qayta bering. |
| **Logo/profil xatosi** | `assets/bot_logo.png` bo‘lmasa ham bot ishlaydi; logda ogohlantirish bo‘ladi. |

### SQLite (muhim)

Ma’lumotlar **`texnopark.db`** ichida. Heroku fayl tizimi **vaqtinchalik** — qayta deploy yoki dyno qayta ishga tushganda ma’lumot **yo‘qolishi mumkin**. Doimiy baza kerak bo‘lsa, keyinroq **Postgres** yoki boshqa DB ulash kerak.

### Deploy fayllari

| Fayl | Vazifasi |
|------|----------|
| `Procfile` | `worker: python -u bot.py` (loglar kechikmasin) |
| `runtime.txt` | Python versiyasi |
| `requirements.txt` | `pip install` |
| `app.json` | Meta, `heroku-24` stack, `heroku/python` buildpack |
