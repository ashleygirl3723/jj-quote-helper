"""
J&J Home Services — Instant Estimate.

A customer-facing quote helper: pick a service, answer a few questions,
get an honest starting-price estimate drawn straight from the J&J price
sheet — then a friendly AI writes it up and answers follow-up questions.

Built for the Hacktoberfest 2026 DEV Challenge, Week 2 ("Side Hustle"):
build something with open-weight models or open-source AI that someone
would actually pay for. (This one is for a real business: J&J Home
Services, Lebanon & Sweet Home, Oregon.)

Open-weight model via OpenRouter's free tier. No API paywall, no card.

Pricing math is deterministic (plain Python from the price sheet) so the
AI can never misquote a number. The AI only writes the friendly message
and answers questions — every price it mentions comes from the sheet.

Run it:
  pip install -r requirements.txt
  streamlit run app.py
"""

import os

import streamlit as st
from openai import OpenAI

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
MODEL = "openrouter/free"  # OpenRouter auto-router: picks a working free open-weight model each call
PHONE = "(408) 823-8144"
SERVICE_AREA = "Lebanon, Sweet Home, and nearby communities"

# ---------------------------------------------------------------------------
# Price sheet (J&J Home Services, effective October 2026).
# Starting prices for typical jobs; firm quote confirmed before work.
# ---------------------------------------------------------------------------
CLEANING_BASE = {
    "Studio / 1 bed, 1 bath": {"standard": 120, "deep": 180},
    "2 bed, 1–2 bath": {"standard": 150, "deep": 225},
    "3 bed, 2 bath": {"standard": 185, "deep": 275},
    "4 bed, 2–3 bath": {"standard": 230, "deep": 345},
}
CLEANING_ADDONS = {
    "Extra bedroom": 25,
    "Extra bathroom": 20,
    "Inside fridge": 25,
    "Inside oven": 25,
    "Interior windows": 40,
}
CLEANING_FREQUENCY_DISCOUNT = {"One-time": 0.0, "Every 2 weeks": 0.10, "Weekly": 0.15}

YARD_MOWING = {
    "Small yard — up to about 5,000 sq ft of lawn": 40,
    "Medium yard — most in-town homes": 45,
    "Large yard — corner lots, acreage edges (from)": 55,
}
YARD_HOURLY = 45  # cleanup, weeding, hedge trimming, leaf cleanup

APPLIANCE_RANGES = {
    "Washer": (150, 350),
    "Dryer": (150, 300),
    "Dishwasher": (100, 300),
}
DIAGNOSTIC_FEE = 50  # credited toward the repair if they go ahead

PRICE_KNOWLEDGE = """J&J HOME SERVICES — PRICE SHEET (effective October 2026, Lebanon & Sweet Home, OR).
Starting prices for typical jobs. Firm quote always confirmed before work begins. No repair ever starts without approval.

HOUSE CLEANING — flat rate by home size:
- Studio / 1 bed, 1 bath: standard $120, deep $180
- 2 bed, 1–2 bath: standard $150, deep $225
- 3 bed, 2 bath: standard $185, deep $275
- 4 bed, 2–3 bath: standard $230, deep $345
- 5+ bed or large home: free quote
Standard clean: kitchens, bathrooms, floors, dusting, mirrors, trash.
Deep clean: everything above plus baseboards, inside appliances, cabinets, built-up grime. Best for first visits, move-ins, move-outs (move-in/out priced as deep clean).
Add-ons: extra bedroom +$25, extra bathroom +$20, inside fridge $25, inside oven $25, interior windows $40.
Regular cleanings: weekly 15% off, every 2 weeks 10% off. Prefer hourly? $25/hr, 2-hour minimum.

YARD WORK — mow, trim, edge, and blow-off included in every mowing visit:
- Small yard mowing: $40/visit; medium: $45/visit; large: from $55/visit
- Cleanup, weeding, hedge trimming, leaf cleanup: $45/hr (or flat quote for big jobs)
- Debris & junk haul-off: priced by load, free quote

APPLIANCE REPAIR — washers, dryers, dishwashers:
- Diagnostic visit: $50, credited toward the repair if they go ahead
- Washer typical total: $150–$350. Dryer: $150–$300. Dishwasher: $100–$300
- Ranges cover most common repairs, parts and labor combined
- If a fix would cost more than half the price of a new appliance, say so honestly and help them weigh replacing it

GOOD TO KNOW:
- Service area: Lebanon, Sweet Home, and nearby communities
- Free quotes on cleaning, yard, and larger jobs — call or text a photo of the job
- No surprises: firm quote first; if something unexpected is found, stop and talk before spending their money
- Heavy buildup, very large yards, or hard-to-reach repairs may be quoted higher — always agreed upfront"""

SYSTEM_PROMPT = """You are the friendly quote helper for J&J Home Services (Lebanon & Sweet Home, Oregon).
Your job: take the estimate details you're given and write a warm, plain-spoken quote message for the customer, then answer their follow-up questions.

Hard rules:
1. NEVER invent a price. Use only the prices in the PRICE SHEET below and the estimate details provided. If the customer asks about something not on the sheet, say it's a free quote and tell them to call or text a photo of the job.
2. Every estimate is a STARTING price for a typical job. Always include the line: "Final quote confirmed before any work begins."
3. Be honest about uncertainty: heavy buildup, very large yards, or tricky repairs may cost more — say so upfront.
4. For appliance repair, always mention the $50 diagnostic (credited toward the repair) and the honest rule: if fixing costs more than half of new, you'll say so.
5. No hype, no pressure. Plain language, short paragraphs. End every quote message with: "Want to book? Call or text (408) 823-8144."
6. Keep answers brief. This is a quote tool, not a chat room.

PRICE SHEET:
""" + PRICE_KNOWLEDGE


def ask(client, messages):
    reply = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
    )
    return reply.choices[0].message.content


def money(n):
    return f"${n:,.0f}"


# ---------------------------------------------------------------------------
# Page setup + state
# ---------------------------------------------------------------------------
st.set_page_config(page_title="J&J Instant Estimate", page_icon="🏠", layout="centered")
st.title("🏠 J&J Home Services")
st.caption("Answer a few questions, get an honest starting-price estimate. No surprises, ever.")

for key, default in [("stage", "form"), ("messages", []), ("estimate_text", ""), ("display_summary", "")]:
    if key not in st.session_state:
        st.session_state[key] = default

api_key = st.sidebar.text_input("OpenRouter API key", type="password",
                                help="Pasted here it lives only in this session. On Streamlit Cloud, use Settings → Secrets instead.")
api_key = api_key or st.secrets.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
st.sidebar.caption(f"📞 {PHONE}\n\n📍 {SERVICE_AREA}")


def generate_estimate():
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    return ask(client, st.session_state.messages)


# ---------------------------------------------------------------------------
# Estimate form
# ---------------------------------------------------------------------------
if st.session_state.stage == "form":
    service = st.selectbox("What do you need?", ["House cleaning", "Yard work", "Appliance repair"])

    estimate_facts = f"SERVICE: {service}\n"

    if service == "House cleaning":
        size = st.selectbox("Home size", list(CLEANING_BASE.keys()) + ["5+ bed or large home"])
        clean_type = st.radio("Clean type", ["Standard", "Deep"], horizontal=True,
                              help="Deep covers baseboards, inside appliances, cabinets, built-up grime. Move-in/out counts as deep.")
        addons = st.multiselect("Add-ons", list(CLEANING_ADDONS.keys()))
        frequency = st.selectbox("How often?", list(CLEANING_FREQUENCY_DISCOUNT.keys()))
        notes = st.text_area("Anything we should know?", height=70,
                             placeholder="Pets, heavy buildup, move-out date…")

        if size == "5+ bed or large home":
            estimate_facts += "HOME SIZE: 5+ bed — FREE QUOTE NEEDED (call/text a photo of the job).\n"
        else:
            base = CLEANING_BASE[size][clean_type.lower()]
            addon_total = sum(CLEANING_ADDONS[a] for a in addons)
            subtotal = base + addon_total
            discount = CLEANING_FREQUENCY_DISCOUNT[frequency]
            total = round(subtotal * (1 - discount))
            estimate_facts += (
                f"HOME SIZE: {size}\nCLEAN TYPE: {clean_type} clean\n"
                f"BASE: {money(base)}\nADD-ONS: {', '.join(addons) if addons else 'none'} "
                f"({money(addon_total)})\nFREQUENCY: {frequency}"
                + (f" ({int(discount*100)}% off)" if discount else "") + "\n"
                f"COMPUTED ESTIMATE: {money(total)}\n"
            )
        estimate_facts += f"CUSTOMER NOTES: {notes.strip() or '(none)'}\n"
        if size == "5+ bed or large home":
            summary = f"🏠 House cleaning — {size}, {clean_type} clean, {frequency}. This one needs a free quote — call or text {PHONE}."
        else:
            addon_text = f" Add-ons: {', '.join(addons)}." if addons else ""
            summary = (f"🏠 House cleaning — {size}, {clean_type} clean, {frequency}.{addon_text} "
                       f"My estimate: **{money(total)}**.")

    elif service == "Yard work":
        task = st.selectbox("What does the yard need?",
                            ["Lawn mowing", "Cleanup / weeding / hedge trimming / leaf cleanup",
                             "Debris & junk haul-off"])
        if task == "Lawn mowing":
            yard_size = st.selectbox("Yard size", list(YARD_MOWING.keys()))
            price = YARD_MOWING[yard_size]
            prefix = "from " if "from" in yard_size else ""
            estimate_facts += f"TASK: mowing — {yard_size}\nCOMPUTED ESTIMATE: {prefix}{money(price)} per visit (mow, trim, edge, blow-off included)\n"
        elif task.startswith("Cleanup"):
            hours = st.number_input("About how many hours of work?", min_value=1, max_value=16, value=2, step=1)
            estimate_facts += (f"TASK: cleanup/weeding/hedge/leaf work\nHOURS: ~{hours} at $45/hr\n"
                               f"COMPUTED ESTIMATE: {money(hours * YARD_HOURLY)} (flat quote possible for big jobs)\n")
        else:
            estimate_facts += "TASK: debris/junk haul-off — FREE QUOTE NEEDED (priced by load size; call/text a photo).\n"
        notes = st.text_area("Anything we should know?", height=70, placeholder="Gate access, steep slope, overgrown areas…")
        estimate_facts += f"CUSTOMER NOTES: {notes.strip() or '(none)'}\n"
        if task == "Lawn mowing":
            from_text = "from " if "from" in yard_size else ""
            summary = f"🌿 Yard work — mowing, {yard_size}. My estimate: **{from_text}{money(price)} per visit**."
        elif task.startswith("Cleanup"):
            summary = f"🌿 Yard work — cleanup/weeding/trimming, about {hours} hour(s). My estimate: **{money(hours * YARD_HOURLY)}**."
        else:
            summary = f"🌿 Yard work — debris/junk haul-off. This one needs a free quote — call or text {PHONE}."

    else:  # Appliance repair
        appliance = st.selectbox("Which appliance?", list(APPLIANCE_RANGES.keys()))
        symptom = st.text_area("What's it doing (or not doing)?", height=80,
                               placeholder="Washer won't drain, dryer has no heat, dishwasher leaks…")
        low, high = APPLIANCE_RANGES[appliance]
        estimate_facts += (
            f"APPLIANCE: {appliance}\nSYMPTOM: {symptom.strip() or '(not described)'}\n"
            f"DIAGNOSTIC: {money(DIAGNOSTIC_FEE)} visit, credited toward the repair\n"
            f"TYPICAL TOTAL REPAIR RANGE: {money(low)}–{money(high)} (parts + labor)\n"
        )
        symptom_text = symptom.strip() or "not described"
        summary = (f"🔧 Appliance repair — {appliance} ({symptom_text}). "
                   f"Diagnostic **{money(DIAGNOSTIC_FEE)}** (credited toward repair); "
                   f"typical total **{money(low)}–{money(high)}**.")

    if st.button("Get my estimate", type="primary", use_container_width=True):
        if not api_key:
            st.error("Add your OpenRouter API key in the sidebar first — the app can't think without one. (Free at openrouter.ai/keys, no credit card.)")
        else:
            st.session_state.messages = [{"role": "user", "content": estimate_facts}]
            st.session_state.display_summary = summary
            try:
                with st.spinner("Writing up your estimate…"):
                    answer = generate_estimate()
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.estimate_text = answer
                st.session_state.stage = "result"
                st.rerun()
            except Exception as e:  # show the real error so you can learn from it
                st.error(f"Something went wrong talking to the AI: {e}")

# ---------------------------------------------------------------------------
# Result + follow-up questions
# ---------------------------------------------------------------------------
else:
    if st.button("↩ Start a new estimate"):
        st.session_state.stage = "form"
        st.session_state.messages = []
        st.session_state.estimate_text = ""
        st.session_state.display_summary = ""
        st.rerun()

    for idx, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            if idx == 0 and m["role"] == "user" and st.session_state.display_summary:
                st.markdown(st.session_state.display_summary)
            else:
                st.markdown(m["content"])

    followup = st.chat_input("Ask about the estimate, what's included, scheduling…")
    if followup:
        st.session_state.messages.append({"role": "user", "content": followup})
        try:
            with st.spinner("Checking the price sheet…"):
                answer = generate_estimate()
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
        except Exception as e:
            st.error(f"Something went wrong talking to the AI: {e}")
            st.session_state.messages.pop()  # drop the failed question so retry is clean
