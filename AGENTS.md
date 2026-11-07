# Security and release baseline

These instructions apply to repository, CI/CD, deployment, publishing automation,
credentials and security changes. Explicit user instructions and higher-priority
instructions prevail. This file grants no account, production or billing authority.

## Scope

- Read repository guidance and inspect the exact target, ref and current settings.
- Preserve unrelated work. Audit-only means read-only. Reuse existing authorization;
  complete reversible preparation before asking for a genuinely missing decision.
- Tie production execution to the reviewed source/content revision and authorized
  scope. Documentation, a passing static scan or a draft PR is not release approval.
- The pilot requires owner approval of each immutable content revision. A model
  confidence score and the old AUTO_PUBLISH flag cannot authorize publication.

## Repository and workflows

- Pin external Actions and reusable workflows to verified full 40-character upstream
  SHAs with version comments. Review ownership/diffs; pinning alone is not trust.
- Default GITHUB_TOKEN to read, grant each job only required access, never write-all;
  use checkout persist-credentials: false unless later commands need credentials.
- Keep untrusted PR validation separate from production secrets, OIDC and persistent
  production runners. No untrusted code through pull_request_target or privileged
  workflow_run. Set timeouts and artifact limits.
- Use fixed executable releases with reviewed checksums, reviewed locks/hashes and
  image digests. Never download and pipe to a shell. Record remaining dependency gaps.
- Preserve protections, native SHA requirements, reviewed action allowlists, isolation
  and exact-source approval gates. Migrate compatible runnable heads before policy
  tightening. Never remove checks or safeguards just to pass CI.
- Workflow/configuration changes require secret-free actionlint and zizmor checks.
  Verify exact resulting revisions and hosted checks after platform policy changes.
  Skipped CI is not passing CI; static scans are not deployment acceptance.
- Maintain reviewed Dependabot Action updates. Do not automatically merge workflow,
  deployment or major dependency updates. Investigate failed checks.
- At first CI/deployment setup, configure suitable checks/native policies within
  scope and verify account/plan support. Never change ownership, billing or visibility
  to obtain a feature without authorization.

## Credentials and production

- Prefer separate restricted automation identities and narrowly scoped short-lived
  credentials/OIDC. Do not claim separation until provisioned and verified.
- Before rotation/revocation inventory owners, consumers and actual read/write needs;
  stage and validate replacements before removing working access. Distinguish
  production fetches from legitimate development pushes.
- Do not retrieve secret values for audits or print keys, tokens, secret environment
  values or authenticated URLs. Use metadata/public fingerprints when sufficient.
- Check release gates at the provider that releases production. GitHub environments
  or CODEOWNERS alone do not prove a Vercel release gate.
- Shaun is the sole human reviewer. Use supported owner-controlled release boundaries
  or an appropriate separate agent identity; label procedural-only controls clearly.
- Do not bypass sandbox, browser, authentication or automatic approval restrictions.
  Report the specific limitation and continue independent authorized preparation.
- Do not commit private article drafts or operational records to this public repo.

## Evidence and closure

- Record target, exact revision, changes, relevant validation, settings readback,
  limitations and next action. Distinguish VERIFIED, INFERRED and UNKNOWN.
- Preserve audit snapshots and add dated implementation records. Keep unresolved
  risks open with an owner and next decision; never silently approve an exception.
- Check relevant drift when touching these areas. Only activate recurring monitoring
  when requested; a documented cadence is not a running schedule.
