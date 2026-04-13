# Guliston Yoshlar Texnoparki — Telegram bot

**aiogram 3** bilan yozilgan anketa boti: OTM tanlash, ism/familiya, telefon, muammo, 2 xonali kod, admin qabul.

## Mahalliy ishga tushirish

1. `pip install -r requirements.txt`
2. `.env.example` ni `.env` qilib nusxalang, `BOT_TOKEN` va `ADMIN_IDS` ni to‘ldiring.
3. `python bot.py`

`.env` va `texnopark.db` repoga kiritilmaydi.

---

## Heroku ga joylash

Bot **polling** ishlatadi — `web` emas, **`worker`** dinamosi kerak.

### 1) Heroku CLI va login

[Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) o‘rnating, keyin:

```bash
heroku login
```

### 2) Ilova yaratish

```bash
cd texnoparkbot
heroku create sizning-app-nomingiz
```

### 3) O‘zgaruvchilar (`.env` o‘rniga)

Heroku Dashboard → ilova → **Settings → Config Vars** yoki CLI:

```bash
heroku config:set BOT_TOKEN="sizning_token" -a sizning-app-nomingiz
heroku config:set ADMIN_IDS="telegram_user_id" -a sizning-app-nomingiz
```

### 4) Deploy

```bash
git push heroku main
```

Agar tarmoq `master` bo‘lsa: `git push heroku master`.

### 5) Worker ni ishga tushirish

```bash
heroku ps:scale worker=1 -a sizning-app-nomingiz
```

Agar `web` dinamosi yaratilgan bo‘lsa (eski loyihalar): `heroku ps:scale web=0 worker=1`.

### 6) Loglar

```bash
heroku logs --tail -a sizning-app-nomingiz
```

### SQLite (muhim)

Hozircha ma’lumotlar **`texnopark.db`** (SQLite) faylida. Heroku fayl tizimi **vaqtinchalik**: dyno qayta ishga tushganda yoki yangi deployda baza **tozalanishi mumkin**.

Doimiy saqlash kerak bo‘lsa — keyinroq **Heroku Postgres** yoki tashqi DB ga o‘tkazish kerak bo‘ladi.

### Fayllar

| Fayl | Vazifasi |
|------|----------|
| `Procfile` | `worker: python bot.py` |
| `runtime.txt` | Python versiyasi |
| `requirements.txt` | Paketlar |
| `app.json` | Deploy haqida meta (ixtiyoriy) |
