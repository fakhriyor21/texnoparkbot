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

### 0) Eng ko‘p xato: noto‘g‘ri buildpack (Node.js)

Agar buildda **`heroku/nodejs`** va **`package.json` topilmadi** degan xato chiqsa — ilovada **Python** buildpack yo‘q.

**Buni bir marta bajaring** (`APP` o‘rniga o‘z ilova nomingiz):

```bash
heroku buildpacks:clear -a APP
heroku buildpacks:set heroku/python -a APP
heroku buildpacks -a APP
```

Chiqishi kerak: **`heroku/python`**.

### 1. Login

```bash
heroku login
```

### 2. Ilova yaratish

```bash
cd texnoparkbot
heroku create sizning-unikal-app-nomingiz
```

Tekshirish: `git remote -v` ( `heroku https://git.heroku.com/...` bo‘lishi kerak).

Agar `heroku` remote yo‘q bo‘lsa:

```bash
heroku git:remote -a sizning-unikal-app-nomingiz
```

### 3. Config Vars (majburiy)

Dashboard: **Settings → Config Vars**:

| Kalit | Qiymat |
|--------|--------|
| `BOT_TOKEN` | @BotFather token |
| `ADMIN_IDS` | Raqam yoki `111,222` |

CLI:

```bash
heroku config:set BOT_TOKEN="TOKEN_BU_YERGA" -a APP
heroku config:set ADMIN_IDS="TELEGRAM_ID" -a APP
```

`BOT_TOKEN` bo‘lmasa, dyno ishga tushganda `bot.py` darhol chiqib ketadi.

**Xavfsizlik:** tokenni **`bot.py` yoki GitHubga qo‘ymang**. Faqat **Heroku → Config Vars** va mahalliy **`.env`** (`.gitignore`da).

### 4. Deploy

```bash
git push heroku main
```

Agar tarmoq `master`: `git push heroku master:main` yoki `git branch -M main`.

### 5. Worker (majburiy)

```bash
heroku ps:scale worker=1 -a APP
```

Keraksiz `web` bo‘lsa: `heroku ps:scale web=0 worker=1 -a APP`.

### 6. Loglar

```bash
heroku logs --tail -a APP
```

Kutiladi: `Bot ishga tushmoqda (aiogram)...`, `Start polling`.

---

### Muammolarni bartaraf etish

| Muammo | Yechim |
|--------|--------|
| **nodejs / package.json** | Yuqoridagi **0-qadam** — `buildpacks:set heroku/python`. |
| **Python versiyasi** | Loyiha ildizida `.python-version` (`3.12`) — [Heroku Python](https://devcenter.heroku.com/articles/python-runtimes). |
| **Crash / R10** | `heroku logs --tail` — `BOT_TOKEN` / `ADMIN_IDS` tekshiring. |
| **Worker yo‘q** | `heroku ps` — `worker` `up`; `ps:scale worker=1`. |

### SQLite

`texnopark.db` Herokuda **vaqtinchalik**; qayta deployda ma’lumot yo‘qolishi mumkin.

### Fayllar

| Fayl | Vazifasi |
|------|----------|
| `Procfile` | `worker: python -u bot.py` |
| `.python-version` | Heroku uchun Python `3.12` (rasmiy usul) |
| `requirements.txt` | Paketlar |
| `app.json` | `heroku/python` buildpack (meta) |
