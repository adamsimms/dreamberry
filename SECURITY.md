# Security Policy

## Supported

| Target | Supported |
|--------|-----------|
| `main` (Modal cron + R2 + window source in this repo) | Yes |
| Assembled `/dreamberry` on [art.adamsimms.xyz](https://art.adamsimms.xyz/dreamberry) | Yes |
| Older local experiments / one-off branches | Best effort |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security-sensitive findings.

Email **hello@adamsimms.xyz** with:

- A description of the vulnerability
- Steps to reproduce
- Impact assessment (credential exposure, XSS, unauthorized R2 writes, etc.)
- Any suggested fix, if you have one

You may also use GitHub [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) on this repository when available.

We will acknowledge receipt and work on a fix as soon as practical. For credential leaks, assume rotation is required immediately.

## In scope

- Secrets handling (`.env`, Modal secrets, R2 API tokens, `HF_TOKEN`)
- R2 write paths and bucket isolation from Cloudberry image buckets
- XSS or injection in `window/` (static shell + drawer)
- GitHub Actions / deploy tokens if workflows are added
- Accidental publication of private archive sidecars or training corpus paths

## Out of scope

- Third-party platforms themselves (Modal, Cloudflare, Open-Meteo, Hugging Face, healthchecks.io) unless this repo’s integration introduced the issue
- The Cloudberry archive product ([pinchards.is](https://github.com/adamsimms/pinchards.is)) — report there or on art
- Model-weight supply chain beyond tokens and download scripts we ship
- Social engineering, physical security, volumetric denial-of-service

## Security practices

### Credentials

- Never commit `.env`, R2 keys, or Modal tokens. Copy from `.env.example` only.
- Prefer Modal Secrets for production; keep local `.env` owner-readable (`chmod 600`).
- Scope R2 API tokens to the **dedicated** Dreamberry bucket (`art-adamsimms-xyz-dreamberry`). Never write into Cloudberry image buckets.
- Rotate any credential that may have been exposed in chat logs, screenshots, or old commits.

### Public surface

- The window **observes** `current/` on R2; it must not gain write credentials in client JS.
- `status.json` and drawer fields may expose generation metadata by design (honesty). Do not put secrets in sidecars.

### Dependencies

- Review dependency and Actions updates before merging, especially anything that runs on Modal with GPU and bucket write access.

## Known limitations

- Dreamberry is a single-artist generative artwork pipeline, not a multi-tenant service.
- Live weather APIs are public; abuse resistance depends on upstream providers and Modal account limits.
- Historical local files under `data/` may contain corpus paths — keep them out of public commits.
