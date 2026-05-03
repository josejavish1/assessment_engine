---
status: "Verified"
owner: "platform-team"
last_verified_against: "2026-05-03"
doc_type: "operational"
applies_to:
  - humans
  - ai-agents
source_of_truth:
  - ../../.github/workflows/
---

# CI/CD Workflow Visualization

This document provides a high-level visualization of the CI/CD pipelines implemented using GitHub Actions. The diagram illustrates the triggers, jobs, and dependencies that form our quality gates and automation processes.

## CI/CD Flow Diagram

The following diagram illustrates the different workflows that are triggered on pull requests and pushes to the `main` and `develop` branches.

```mermaid
graph TD
    subgraph "Trigger: Pull Request (to main/develop)"
        PR[Pull Request]
        PR -->|Parallel Jobs| QualityGates
    end

    subgraph "Primary Quality Gates"
        QualityGates(fa:fa-shield-halved Quality Gates)
        QualityGates --> CI[CI Workflow: ci.yml]
        QualityGates --> Quality[Quality Workflow: quality.yml]
        QualityGates --> Typing[Typing Workflow: typing.yml]
        QualityGates --> Docs[Docs Gov. Workflow: docs-governance.yml]
        
        CI --> Job_Test(test)
        Quality --> Job_Quality(quality)
        Typing --> Job_Typing(typing)
        Docs --> Job_Docs(docs-governance)
    end
    
    subgraph "Conditional Trigger: PR with AI changes"
        PR_AI[PR with changes in prompts/, schemas/, etc.]
        PR_AI --> AgentEvals[Agent Evals Workflow: agent-evals.yml]
        AgentEvals --> Job_Evals(evals)
    end

    subgraph "Trigger: Push to main"
        PushMain[Push to main]
        PushMain --> Reconciler[PR Reconciler: orchestrator-pr-reconcile.yml]
        Reconciler --> Job_Reconcile(reconcile)
    end

    subgraph "Trigger: Nightly Schedule"
        Schedule[Nightly Cron]
        Schedule --> AgentEvals
    end

    style QualityGates fill:#f9f,stroke:#333,stroke-width:2px
```
