# Dreamberry

The dead [Cloudberry](https://art.adamsimms.xyz/cloudberry/archive/) camera **dreaming** — a labeled generative window on Pinchard's Island, Newfoundland, conditioned by live weather.

**Canonical URL (intended):** [art.adamsimms.xyz/dreamberry](https://art.adamsimms.xyz/dreamberry)

This is a **sibling** to the Cloudberry archive, not an extension of it. The archive stays sacred and separate.

## Docs

- [Project brief](docs/DREAMBERRY.md) — concept, architecture, dial, failure modes, infra
- [Weather → image schema](docs/DREAMBERRY-WEATHER-SCHEMA.md) — symmetric train/live conditioning

## Stack (v1)

- **Generation:** SDXL + ControlNet + IP-Adapter + weather-nearest real-frame anchor + LoRA (mid-dial)
- **Compute / cron:** Modal
- **Storage / window:** Cloudflare R2 + Pages (under art.adamsimms.xyz)
- **Tracking:** GitHub Issues (milestones `v0-research`, `v1-window`, `v2-forgetting`)

## Status

Build kickoff. See Issues.
