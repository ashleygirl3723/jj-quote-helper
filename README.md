# J&J Home Services — Instant Estimate 🏠

A customer-facing quote helper for J&J Home Services (Lebanon & Sweet Home,
Oregon). Pick a service, answer a few questions, and get an honest
starting-price estimate drawn straight from the J&J price sheet — then a
friendly AI writes it up and answers follow-up questions.

Built for the **Hacktoberfest 2026 DEV Challenge, Week 2 ("Side Hustle")** —
build something with open-weight models or open-source AI that someone would
actually pay for. This one is for a real business.

## What it does

- **House cleaning** — flat-rate estimate by home size, clean type
  (standard/deep), add-ons, and frequency discounts (weekly 15% off,
  biweekly 10% off)
- **Yard work** — mowing by yard size, hourly cleanup/weeding/hedging,
  haul-off routed to a free quote
- **Appliance repair** — $50 diagnostic (credited toward repair) plus the
  honest typical range, with the "if fixing costs more than half of new,
  we'll tell you" rule

The pricing math is **deterministic Python from the price sheet**, so the AI
can never misquote a number. The open-weight model only writes the friendly
message and answers questions — every price it mentions comes from the
sheet. Jobs that don't fit the sheet (5+ bed homes, haul-off) route to a
free quote by call/text instead of a guessed number.

## How it's built

- **Streamlit** frontend, Python, deploys free on Streamlit Cloud
- **Open-weight models via OpenRouter's free tier** (`openrouter/free`
  auto-router picks a working free open-weight model per call) — no API
  paywall, no credit card
- The whole stack costs **$0**: the margin story judges love — open weights
  keep the tool free, which is the only way a small home-services business
  can afford to run one

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Add your OpenRouter API key in the sidebar (free at
[openrouter.ai/keys](https://openrouter.ai/keys), no credit card), or on
Streamlit Cloud paste it once under **Settings → Secrets** as
`OPENROUTER_API_KEY`.
