#!/bin/bash
set -euo pipefail

gh pr list 
  --search "is:open -is:draft -label 'no-auto-update'" 
  --json number,headRefName 
  --jq '.[] | "\(.number) \(.headRefName)"' |
while read -r pr_number pr_branch; do
  echo "::group::Processing PR #${pr_number} (branch: ${pr_branch})"

  # Ensure we are on a clean main branch before starting
  git checkout -f main
  git reset --hard origin/main

  git fetch origin "${pr_branch}:${pr_branch}"
  
  merge_base=$(git merge-base origin/main "${pr_branch}")
  main_head=$(git rev-parse origin/main)

  if [ "$merge_base" = "$main_head" ]; then
    echo "Branch '${pr_branch}' is already up-to-date with 'main'."
    echo "::endgroup::"
    continue
  fi

  echo "Branch '${pr_branch}' needs updating. Rebasing onto 'main'."

  git checkout "${pr_branch}"
  
  if ! git rebase origin/main; then
    echo "::error::Conflict detected while rebasing '${pr_branch}'. Aborting rebase."
    gh pr comment "${pr_number}" --body "Automatic rebase failed due to merge conflicts. Please resolve them manually and push the changes."
    git rebase --abort
    echo "::endgroup::"
    continue
  fi

  git push origin "${pr_branch}" --force-with-lease
  echo "Successfully updated branch '${pr_branch}'."
  echo "::endgroup::"
done
