"""
Outside Collective: community events performance read-out.

Joins Posh ticketing data (events, sources) with Instagram content data and answers:
  Growth:      Is the community growing, and are people coming back?
  Funnel:      How do event-page visits convert to tickets, and tickets to attendance?
  Operations:  How far ahead do people commit, and how full do events get?
  Economics:   What do paid vs free events contribute?
  Content:     Which Instagram posts and formats travel furthest?

All figures are aggregates. No attendee or follower data is stored in this repo.
Revenue, price, fee and refund-amount fields are illustrative, not Outside Collective's actual financials.
Usage (from the repo root):  python analysis/analyze.py
"""
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "images"
IMG.mkdir(exist_ok=True)
AS_OF = pd.Timestamp("2026-11-23")

INK, MUTED, GRID = "#1f2937", "#6b7280", "#e5e7eb"
GREEN, DEEP, SUN, CALM, CORAL = "#2f6b3f", "#14532d", "#e0a526", "#cbd5e1", "#d9603b"
TYPE_COLORS = {"social": "#7c3aed", "outdoor": GREEN, "ticketed_outing": SUN, "scavenger_hunt": "#0891b2", "cafe_crawl": CORAL}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
})


def title(ax, text, sub=None):
    ax.set_title(text, loc="left", color=INK, fontweight="bold", pad=20 if sub else 8)
    if sub:
        ax.text(0, 1.02, sub, transform=ax.transAxes, color=MUTED, fontsize=9)


def save(fig, name):
    fig.savefig(IMG / name, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def short_name(n):
    n = re.sub(r"[^\w\s&:|'\-]", "", n).strip()
    n = re.sub(r"^(OUTSIDE COLLECTIVE|Outside Collective|An Outside Collective Linkup)\s*[:|]\s*", "", n, flags=re.I).strip()
    small = {"of", "the", "on", "in", "and", "a", "at"}
    words = n.title().replace("'S", "'s").split()
    return " ".join(w if i in (0, len(words) - 1) or w.lower() not in small else w.lower() for i, w in enumerate(words))


ev = pd.read_csv(ROOT / "data" / "oc_events.csv", parse_dates=["event_date"])
src = pd.read_csv(ROOT / "data" / "oc_event_sources.csv")
posts = pd.read_csv(ROOT / "data" / "oc_instagram_posts.csv", parse_dates=["post_date"])
monthly = pd.read_csv(ROOT / "data" / "oc_instagram_monthly.csv")
ev["name"] = ev["event_name"].map(short_name)
ev["held"] = ev["event_date"] <= AS_OF
ev["paid"] = ev["net_revenue"] > 0
ev["conversion"] = ev["tickets_sold"] / ev["page_views"]
ev["sell_through"] = ev["tickets_sold"] / ev["capacity"]
ev["show_rate"] = ev["check_ins"] / ev["tickets_sold"]
ev["buyers"] = ev["first_time_buyers"] + ev["returning_buyers"]
ev["returning_share"] = ev["returning_buyers"] / ev["buyers"]
lead_cols = ["orders_0d", "orders_1_2d", "orders_3_7d", "orders_8_14d", "orders_15d_plus"]
ev["orders"] = ev[lead_cols].sum(axis=1)
ev["early_share"] = (ev["orders_8_14d"] + ev["orders_15d_plus"]) / ev["orders"]
held = ev[ev["held"]]
F = {}

# ------------------------------------------------------------- headline
F["headline"] = {
    "events_held": int(held.shape[0]), "events_upcoming": int((~ev["held"]).sum()),
    "tickets": int(ev["tickets_sold"].sum()), "page_views": int(ev["page_views"].sum()),
    "net_revenue": round(float(ev["net_revenue"].sum()), 2),
    "first_event": ev["event_date"].min().strftime("%b %Y"),
    "avg_tickets_per_event_held": round(held["tickets_sold"].mean()),
    "unique_attendees_reported": 498,  # Posh account total (unique people)
}

# ------------------------------------------------------------- funnel
F["funnel"] = {
    "page_to_ticket_pct": round(ev["tickets_sold"].sum() / ev["page_views"].sum() * 100, 1),
    "best_conversion": [ev.loc[ev["conversion"].idxmax(), "name"], round(ev["conversion"].max() * 100)],
    "worst_conversion": [ev.loc[ev["conversion"].idxmin(), "name"], round(ev["conversion"].min() * 100)],
    "conv_free_pct": round(held.loc[~held["paid"], "tickets_sold"].sum() / held.loc[~held["paid"], "page_views"].sum() * 100, 1),
    "conv_paid_pct": round(ev.loc[ev["paid"], "tickets_sold"].sum() / ev.loc[ev["paid"], "page_views"].sum() * 100, 1),
    "events_with_checkin": int(held["check_ins"].notna().sum()),
    "show_rate_where_measured_pct": round(held["check_ins"].sum() / held.loc[held["check_ins"].notna(), "tickets_sold"].sum() * 100),
    "show_rate_range": [round(held["show_rate"].min() * 100), round(held["show_rate"].max() * 100)],
}

# ------------------------------------------------------------ operations
cap = ev[ev["capacity"].notna()]
F["operations"] = {
    "capped_events": int(len(cap)), "sold_out": int((cap["sell_through"] >= 1).sum()),
    "avg_sell_through_pct": round(cap["sell_through"].mean() * 100),
    "early_share_paid_pct": round((ev.loc[ev["paid"], "orders_8_14d"].sum() + ev.loc[ev["paid"], "orders_15d_plus"].sum()) / ev.loc[ev["paid"], "orders"].sum() * 100),
    "early_share_free_pct": round((held.loc[~held["paid"], "orders_8_14d"].sum() + held.loc[~held["paid"], "orders_15d_plus"].sum()) / held.loc[~held["paid"], "orders"].sum() * 100),
    "last_week_share_free_pct": round((held.loc[~held["paid"], ["orders_0d", "orders_1_2d", "orders_3_7d"]].sum().sum()) / held.loc[~held["paid"], "orders"].sum() * 100),
    "upcoming_sell_through_pct": round(float(ev.loc[~ev["held"], "sell_through"].iloc[0]) * 100),
}

# ------------------------------------------------------------- retention
F["retention"] = {
    "returning_share_first3_pct": round(ev.iloc[:3]["returning_buyers"].sum() / ev.iloc[:3]["buyers"].sum() * 100),
    "returning_share_last3_pct": round(ev.iloc[-3:]["returning_buyers"].sum() / ev.iloc[-3:]["buyers"].sum() * 100),
    "returning_buyers_total": int(ev["returning_buyers"].sum()),
}

# ------------------------------------------------------------- economics
paid = ev[ev["paid"]]
F["economics"] = {
    "paid_events": int(len(paid)), "free_events": int((~ev["paid"]).sum()),
    "revenue_paid": round(float(paid["net_revenue"].sum()), 2),
    "revenue_per_paid_ticket": round(float(paid["net_revenue"].sum() / paid["tickets_sold"].sum()), 2),
    "largest_event_revenue": [paid.loc[paid["net_revenue"].idxmax(), "name"], round(float(paid["net_revenue"].max()), 2)],
    "refund_rate_pct": round(ev["refund_count"].sum() / ev["orders"].sum() * 100, 1),
}

# ------------------------------------------------------------- acquisition
s = src.groupby("source")["tickets"].sum()
F["acquisition"] = {
    "explore_share_pct": round(s.get("posh_explore", 0) / s.sum() * 100),
    "explore_share_free_pct": round(src[src["event_id"].isin(ev.loc[~ev["paid"], "event_id"]) & (src["source"] == "posh_explore")]["tickets"].sum()
                                    / src[src["event_id"].isin(ev.loc[~ev["paid"], "event_id"])]["tickets"].sum() * 100),
    "explore_share_paid_pct": round(src[src["event_id"].isin(paid["event_id"]) & (src["source"] == "posh_explore")]["tickets"].sum()
                                    / src[src["event_id"].isin(paid["event_id"])]["tickets"].sum() * 100),
}

# ------------------------------------------------------------- content
p = posts.copy()
p["eng"] = p["likes"] + p["comments"] + p["shares"]
by_fmt = p.groupby("format").agg(posts=("post_date", "count"), views=("impressions", "median"), shares=("shares", "median"), eng=("eng", "median"))
by_purpose = p.groupby("purpose").agg(posts=("post_date", "count"), views=("impressions", "median"), shares=("shares", "median"), eng=("eng", "median"))
F["content"] = {
    "posts": int(len(p)), "views": int(p["impressions"].sum()), "likes": int(p["likes"].sum()), "shares": int(p["shares"].sum()),
    "posts_per_month": round(len(p) / p["post_date"].dt.to_period("M").nunique(), 1),
    "median_views_by_format": by_fmt["views"].round().to_dict(), "median_shares_by_format": by_fmt["shares"].to_dict(),
    "median_shares_by_purpose": by_purpose["shares"].to_dict(), "median_views_by_purpose": by_purpose["views"].round().to_dict(),
    "peak_month": monthly.loc[monthly["impressions"].idxmax(), "month"],
    "top_post": p.loc[p["impressions"].idxmax(), ["post_date", "format", "purpose", "impressions"]].astype(str).to_dict(),
}

# ================================================================= charts
order = ev.sort_values("event_date")
import textwrap
labels = ["\n".join(textwrap.wrap(n, 11)) + f"\n{d:%b %d}" for n, d in zip(order["name"], order["event_date"])]

# 1. Funnel per event: page views vs tickets, with conversion
fig, ax = plt.subplots(figsize=(12, 4.6))
x = np.arange(len(order))
ax.bar(x, order["page_views"], color=CALM, width=0.7, label="Event page visits")
ax.bar(x, order["tickets_sold"], color=[TYPE_COLORS[t] for t in order["event_type"]], width=0.7, label="Tickets")
for i, r in enumerate(order.itertuples()):
    ax.text(i, r.page_views + 25, f"{r.conversion:.0%}", ha="center", fontsize=8, color=INK)
ax.set_xticks(x, labels, fontsize=7.5)
ax.set_ylabel("Visits / tickets")
ax.legend(frameon=False, fontsize=8, loc="upper left")
title(ax, "From event page to ticket", f"{F['funnel']['page_to_ticket_pct']}% of event-page visits became tickets overall · label = conversion per event")
save(fig, "funnel_by_event.png")

# 2. Retention: first-time vs returning buyers per event
fig, ax = plt.subplots(figsize=(12, 4.4))
ax.bar(x, order["first_time_buyers"], color=CALM, width=0.7, label="First-time buyers")
ax.bar(x, order["returning_buyers"], bottom=order["first_time_buyers"], color=GREEN, width=0.7, label="Returning buyers")
for i, r in enumerate(order.itertuples()):
    ax.text(i, r.buyers + 2, f"{r.returning_share:.0%}", ha="center", fontsize=8, color=GREEN)
ax.set_xticks(x, labels, fontsize=7.5)
ax.set_ylabel("Unique buyers")
ax.legend(frameon=False, fontsize=8, loc="upper left")
title(ax, "A returning core is forming",
      f"Returning buyers rose from {F['retention']['returning_share_first3_pct']}% of buyers (first 3 events) to {F['retention']['returning_share_last3_pct']}% (last 3)")
save(fig, "retention.png")

# 3. Booking lead time per event: planned outings sell early, drop-in socials sell late
lt = order[order["held"] | (order["event_date"] > AS_OF)].copy()
lt = lt.sort_values("early_share")
fig, ax = plt.subplots(figsize=(9, 4.2))
ax.barh(lt["name"], lt["early_share"] * 100, color=[TYPE_COLORS[t] for t in lt["event_type"]], height=0.6)
for i, v in enumerate(lt["early_share"] * 100):
    ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=8, color=MUTED)
ax.axvline(50, color=GRID, linestyle="--")
ax.set_xlim(0, 110)
ax.set_xlabel("Share of orders placed 8+ days before the event")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=c, label=k.replace("_", " ").capitalize()) for k, c in TYPE_COLORS.items()], frameon=False, fontsize=8, loc="lower right")
title(ax, "Planned outings sell early; drop-in socials sell late",
      "Trips, picnics and crawls give 2+ weeks of planning certainty; socials fill in the final week")
save(fig, "booking_lead_time.png")

# 4. Instagram: monthly views + posts, and format/purpose medians
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), gridspec_kw={"width_ratios": [1.4, 1]})
m = monthly.copy()
xm = np.arange(len(m))
ax1.bar(xm, m["impressions"] / 1000, color=GREEN, width=0.6)
ax1b = ax1.twinx()
ax1b.plot(xm, m["posts"] + m["reels"], color=SUN, marker="o", linewidth=2)
ax1b.set_ylabel("Posts published", color=SUN)
ax1b.spines["top"].set_visible(False)
ax1.set_xticks(xm, [pd.Period(v).strftime("%b") + ("*" if v == m["month"].iloc[-1] else "") for v in m["month"]])
ax1.set_ylabel("Views (thousands)")
title(ax1, "Instagram views by month", "Bars = views · line = posts and reels published · *month to date")
pv = p.groupby(["purpose"]).agg(views=("impressions", "median"), shares=("shares", "median")).reindex(["event_promo", "event_recap", "community"])
xp = np.arange(len(pv))
ax2.bar(xp, pv["shares"], width=0.55, color=[CORAL, CALM, CALM])
for i, r in enumerate(pv.itertuples()):
    ax2.text(i, r.shares + 0.3, f"{r.shares:.1f} shares\n{r.views / 1000:.1f}K views", ha="center", fontsize=8, color=INK)
ax2.set_xticks(xp, ["Event promo", "Event recap", "Community"])
ax2.set_ylabel("Median shares per post")
ax2.set_ylim(0, pv["shares"].max() * 1.35)
title(ax2, "Promos get shared", "Median per post, by purpose")
fig.subplots_adjust(wspace=0.45)
save(fig, "instagram.png")

print(json.dumps(F, indent=2, default=str))
print(order[["name", "event_type", "tickets_sold", "page_views", "conversion", "sell_through", "show_rate", "returning_share", "early_share", "net_revenue"]].round(2).to_string())
print(by_fmt.round(1))
print(by_purpose.round(1))

# ------------------------------------------------ export for the dashboard
out = {
    "as_of": AS_OF.strftime("%Y-%m-%d"),
    "unique_attendees": 498,
    "events": json.loads(ev.assign(event_date=ev["event_date"].dt.strftime("%Y-%m-%d"))[
        ["event_id", "name", "event_date", "event_type", "neighborhood", "capacity", "tickets_sold", "comp_tickets", "net_revenue",
         "refund_count", "check_ins", "page_views", "first_time_buyers", "returning_buyers", "held", "paid"] + lead_cols
    ].to_json(orient="records")),
    "sources": json.loads(src.to_json(orient="records")),
    "posts": json.loads(posts.assign(post_date=posts["post_date"].dt.strftime("%Y-%m-%d"))[
        ["post_date", "format", "purpose", "impressions", "likes", "comments", "shares"]].to_json(orient="records")),
    "monthly": json.loads(monthly[["month", "impressions", "posts", "reels", "likes", "comments", "shares"]].to_json(orient="records")),
}
(ROOT / "docs" / "data.json").write_text(json.dumps(out, separators=(",", ":")))
