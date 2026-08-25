#!/usr/bin/env bash
# Apply the branch protection tech.md section 17 requires:
# pull requests only, merge on green CI, linear history, no direct push.
#
# Run once after the repository exists on github:
#   gh auth login
#   .github/branch-protection.sh owner/repo
set -euo pipefail

REPO="${1:?usage: branch-protection.sh owner/repo}"
BRANCH="${2:-main}"

# Names must match the `name:` of each job in ci.yml.
read -r -d '' PAYLOAD <<'JSON' || true
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "ruff and mypy",
      "migrations and pytest",
      "playwright on the built image",
      "docker build"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
JSON

# required_approving_review_count is 0 on purpose: the team is one person, and
# a review requirement they cannot satisfy would block every merge. The pull
# request itself is still mandatory, and CI still has to be green.

echo "$PAYLOAD" | gh api -X PUT "repos/${REPO}/branches/${BRANCH}/protection" --input -
echo "protection applied to ${REPO}@${BRANCH}"
