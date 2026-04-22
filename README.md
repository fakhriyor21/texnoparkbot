# Guliston Yoshlar Texnoparki — Telegram bot

aiogram 3: OTM → ism/familiya → telefon → muammo → 2 xonali kod; kanal va Instagram obunasi; admin qabul/rad.

## Mahalliy

```bash
pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN va ADMIN_IDS
python bot.py
```

Standart kanal: [@sirdaryotexnopark](https://t.me/sirdaryotexnopark) · Instagram: `guliston_yoshlar_texnoparki` — kodda default; `.env` bilan almashtirish mumkin.

## Heroku

**Majburiy Config Vars:** `BOT_TOKEN`, `ADMIN_IDS`

```bash
heroku buildpacks:set heroku/python -a APP
heroku config:set BOT_TOKEN="..." ADMIN_IDS="6777571934" -a APP
git push heroku main
heroku ps:scale worker=1 web=0 -a APP
heroku logs --tail -a APP
```

Buildpack `heroku/nodejs` bo‘lsa: `heroku buildpacks:clear` va yuqoridagi Python buildpack.

**Worker** (`Procfile`): `worker: python -u bot.py` — faqat `worker` dyno ishlaydi.

SQLite `texnopark.db`: arizalar (`submissions`) va FSM holatlari (`fsm_state`). Herokuda ephemeral disk — deploy/qayta ishga tushishda fayl tiklanmasligi mumkin.
