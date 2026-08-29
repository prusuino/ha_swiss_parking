# Security Policy

## Supported Versions

Only the latest release is supported. Please update to the latest version before reporting an issue.

## Reporting a Vulnerability

This integration only reads publicly published data. It polls the five city feeds listed in [NOTICE.md](NOTICE.md) — pls-zh.ch (Zürich), data.bs.ch (Basel), stadtplan.winterthur.ch (Winterthur), parking-bern.ch (Bern) and data.tg.ch (Frauenfeld) — with plain, unauthenticated GET requests over HTTPS. Those requests carry no credentials and no user data; the only thing that leaves your instance is which of the fixed feed URLs is fetched. Your home coordinates are used locally only, for the distance state of the map markers, and are never sent anywhere. The integration does not handle credentials or personal data and has no write access to any external system. If you still believe you have found a security issue (e.g. in how data is parsed or how entities are exposed), please report it privately via [GitHub Security Advisories](../../security/advisories/new) rather than opening a public issue.

For anything that is not security-sensitive (bugs, feature requests), please use the regular [Issues](../../issues) tab instead.
