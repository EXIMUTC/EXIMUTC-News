# Website News continuation state

Updated: 2026-09-30 06:10 UTC.

Production: https://news.eximutc.com/
Latest article: https://news.eximutc.com/articles/the-smithsonian-displays-a-168-carat-mackay-emerald-necklace-ab0441f7.html

Completed:
- Existing DNS CNAME news.eximutc.com -> eximutc.github.io verified through Google's public DNS response. No DNS changes were necessary.
- GitHub Pages custom domain saved as news.eximutc.com; DNS check successful; Enforce HTTPS enabled.
- Publisher canonical URLs, sitemap and robots switched to the production domain.
- Public publishing workflow runs every 3 hours and verifies the latest public article, body, market view, date, metadata, index and SVG image. Fails if no new publication for over 12 hours.
- Workflow 36676622748 / job 109762867792 passed the HTTPS production checker at 2026-09-30T06:07:17Z. Published HTML commit 62bd944.

Verification limitation:
- This environment's cloud browser and local outbound requests display a Site Unavailable intermediary for the custom domain. GitHub Actions fetched and verified the real HTTPS article and index successfully. Do not claim a visual browser check of the custom domain has passed.

Remaining:
- Private orchestrator PR #32 is still draft, unmerged, at 4f826f419170902e6277ca255ff34ce2a958cbb1. Its direct cross-repository publication requires the scoped EXIMUTC_NEWS_DEPLOY_KEY secret and matching write deploy key; both must be set before merging. Update that PR's production-check base to https://news.eximutc.com/ before executing.
- Existing ChatGPT control automation 6abc9d4b5ad8819181793f80da6a5f33 has been updated to the production domain and an immediate execution requested. Its completed run and future automatic transfer are not yet verified.
- Do not mark the complete autonomous pipeline READY until private -> public -> production publication succeeds without manual transfer.
- Do not reattempt GoDaddy cloud login: it rejects this cloud browser and DNS is already correct.
- Leave social and WhatsApp code, credentials and routing untouched.
