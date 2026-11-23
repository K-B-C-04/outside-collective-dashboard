# Data notes

**As of:** November 23, 2026 · **Sources:** Posh organizer dashboard (ticketing) and Instagram (content performance)

## Privacy

- The repo contains **aggregates only**: totals per event, per sales source, per post and per month.
- No attendee, buyer or follower names, emails, phone numbers, handles, order IDs or comment text are stored anywhere in it.
- **Financial columns are illustrative.** In `oc_events.csv`, `min_price`, `max_price`, `gross_revenue`, `fees`, `refund_amount` and `net_revenue` are not Outside Collective's actual figures. Free events are shown as free. Ticket counts, refund counts and all other columns are actual.

## Posh: events (`oc_events.csv`, `oc_event_sources.csv`)

- **Coverage:** all 11 events on the account, from April 12, 2026 to January 15, 2027. The January event was on sale at the time of the pull, so its sales and buyer counts are partial.
- **tickets_sold:** net tickets, excluding canceled and refunded tickets. Free RSVP tickets are included.
- **capacity:** blank where no ticket cap was set.
- **check_ins:** tickets scanned at the door. Blank where tickets weren't scanned, so attendance at those events is unknown. This is why check-in rates are reported only for the 4 events that scanned.
- **page_views:** all-time event page visits.
- **orders_\*d:** orders by days between purchase and event start (`0` = same day, including at-door sales).
- **first_time_buyers / returning_buyers:** unique buyer accounts per event. "Returning" means the account bought a ticket to an earlier Outside Collective event. This counts buyers, not guests.
- **Unique attendees (498):** the account-level total of unique people, which is lower than total tickets (652) because repeat attendees are counted once.
- **Sources:** `event_page` is direct traffic, including shared links and the Instagram bio; `posh_explore` is Posh marketplace discovery; `in_person` is pay-at-door. Posh can't separate Instagram traffic from other direct traffic, because no channel-specific tracking links were in use. Source totals can run slightly above `tickets_sold` because they include tickets later canceled or refunded.
- **event_type:** assigned from each event's format (social, outdoor, ticketed outing, scavenger hunt, cafe crawl).

## Instagram (`oc_instagram_posts.csv`, `oc_instagram_monthly.csv`)

- **Coverage:** 66 feed posts and reels from February 9 to November 23, 2026 (39 reels, 15 images, 12 carousels). Story highlights and posts owned by partner accounts are excluded.
- **impressions:** Instagram views. Blank for 3 posts where views weren't returned; those posts are excluded from view totals and medians.
- **purpose:** each post is classified as `event_promo` (advertises an upcoming event), `event_recap` (documents a past event) or `community` (general brand or community content).
- **Not available at this grain:** reach, profile visits, follows per post, follower counts by month, saves (returned as 0), and story metrics. These columns are blank rather than estimated.

## Known gaps

- **Attendance** is only measured where tickets were scanned (4 of 10 events).
- **Instagram-to-ticket attribution** isn't possible yet; see the recommendation on tracking links in the README.
- **Audience demographics** (location, age) were not included.
