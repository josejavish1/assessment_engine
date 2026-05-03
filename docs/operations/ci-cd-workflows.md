---
status: "Verified"
owner: "platform-team"
last_verified_against: "2026-05-03"
applies_to:
  - humans
  - ai-agents
source_of_truth:
  - .github/workflows/agent-evals.yml
  - .github/workflows/ci.yml
  - .github/workflows/docs-governance.yml
  - .github/workflows/orchestrator-pr-reconcile.yml
  - .github/workflows/quality.yml
  - .github/workflows/typing.yml
doc_type: "operational"
---

# CI/CD Workflows

This document provides a high-level overview of the CI/CD pipelines and quality gates implemented in this repository using GitHub Actions. The primary goal of our CI/CD system is to ensure code quality, stability, and adherence to architectural guidelines through a series of automated checks that run on every pull request.

## High-Level Flow Diagram

The following diagram illustrates the primary workflows. Most are triggered on pull requests against the `main` and `develop` branches and run in parallel as status checks.

```mermaid
graph TD
    subgraph Trigger
        A[Push or Open PR to main/develop]
    end

    subgraph "CI/CD Pipeline (Runs in Parallel)"
        A --> B[CI: Tests & Smoke Run];
        A --> C[Quality: Incremental Checks];
        A --> D[Typing: Incremental Type Check];
        A --> E[Docs: Governance Check];
        A --> F[Agent Evals (Conditional on file paths)];
    end
    
    subgraph "Other Triggers"
        G[Nightly Schedule] --> F;
        H[Merge to main] --> I[Auto-reconcile open PRs];
    end

    B --> Z{PR Status};
    C --> Z;
    D --> Z;
    E --> Z;
    F --> Z;
```

## Workflow Descriptions

-   **CI (`ci.yml`):** The core integration pipeline. It runs the full `pytest` suite, executes a smoke test (`regenerate_smoke_artifacts --dry-run`), and validates documentation governance. This is the main gate for overall system health.

-   **Quality (`quality.yml`):** Performs incremental checks on the files changed in the pull request. This includes running linters, formatters, and a "Golden Path" check to enforce architectural fitness rules.

-   **Typing (`typing.yml`):** Runs an incremental static type check using `mypy` on the changed files, ensuring type safety.

-   **Docs Governance (`docs-governance.yml`):** A dedicated check to ensure that all documentation files (`.md`) have valid YAML front matter and adhere to the project's documentation standards.

-   **Agent Evals (`agent-evals.yml`):** A specialized and longer-running workflow that evaluates the performance of the AI agents. It runs conditionally on PRs that modify core agent logic and also runs nightly to monitor for regressions.

-   **PR Auto-Reconciler (`orchestrator-pr-reconcile.yml`):** This workflow is not a quality gate. It triggers after a merge to `main` and automatically updates all other open pull requests with the latest changes from `main` to prevent merge conflicts and ensure PRs are tested against the most recent codebase.
