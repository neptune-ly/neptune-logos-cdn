# Neptune merchant logos — CDN copy

Public, read-only copy of the merchant-logo registry, served by GitHub Pages behind Cloudflare at
`https://logos-cdn.neptune.ly/v1/index.json` and `.../v1/logo/<hash>-<96|256>.webp`.

The source of truth and the registration/staff portals are at `https://logos.neptune.ly`
(repository `neptune-ly/neptune-merchant-logos`). `.github/workflows/mirror.yml` pulls from there
every 10 minutes; nothing here is edited by hand. Logos are named by content hash and never change.
