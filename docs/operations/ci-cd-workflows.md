---
status: "Draft"
owner: "platform-team"
last_verified_against: "2026-05-03"
doc_type: "operational"
---

# CI/CD Workflow Visualization

This document provides a high-level visualization of the CI/CD pipelines implemented using GitHub Actions. The diagram illustrates the triggers, jobs, and dependencies that form our quality gates and automation processes.

## CI/CD Flow Diagram

The following diagram illustrates the different workflows that are triggered on pull requests and pushes to the `main` and `develop` branches.

```mermaid
graph TD
    subgraph "Pull Request Triggered Workflows"
        A[Pull Request to main/develop] --> B{CI};
        A --> C{Docs Governance};
        A --> D{Quality Gate};
        A --> E{Typing};
        A --> F{Agent Evals (conditional)};

        B --> B1[Run pytest];
        B --> B2[Run smoke dry-run];
        B --> B3[Validate doc governance];

        C --> C1[Validate doc governance];

        D --> D1[Incremental quality check];
        D --> D2[Golden path check];

        E --> E1[Incremental type check];

        F --> F1[Run agent evals];
    end

    subgraph "Post-Merge Workflows"
        G[Push to main] --> H{PR Reconciler};
        H --> H1[Reconcile open PRs];
    end

    subgraph "Scheduled Workflows"
        I[Nightly Schedule] --> F;
    end
```
