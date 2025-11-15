# Phase 1 Verification Checklist

| Item | Verification Steps | Owner | Status / Notes |
| --- | --- | --- | --- |
| Environment bootstrap | Run `./scripts/bootstrap_env.sh`, confirm containers healthy, create superuser, and call `curl -u <user>:<pass> http://localhost:8000/api/user/` (expect HTTP 200). | Backend Lead |  |
| CI harness | Open a test PR to trigger `.github/workflows/ci.yml`, ensure both backend and frontend jobs pass, and confirm README badge turns green. | DevOps Lead |  |
| Secrets workflow | Copy `.env.example` → `.env`, update passwords + storage path, verify `.env` stays untracked, and document secret sources per `docs/config.md`. | Backend Lead |  |

Record any issues, remediation steps, and timestamps in the Status column so downstream teams can trust the baseline.






