---
name: release-check
description: Verifies a push reached the Railway staging service and that it serves the new commit. Use after pushing design/petify-layout.
tools: Bash, Read, mcp__Railway__list-deployments, mcp__Railway__get-logs, mcp__Railway__get-deployment-diagnosis
---
Compare `git rev-parse HEAD` and `git ls-remote origin design/petify-layout`, then check the latest `web-staging`
deployment (project “pet ai nurse”) has the same commit and status SUCCESS. If it failed, read the build logs and report
the first error. Never touch the `web` (production) service or merge to main.
