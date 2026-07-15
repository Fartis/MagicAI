# Repository health and community readiness

MagicAI is intended to remain maintainable even when development is no longer concentrated in one person's hands. Repository health therefore advances alongside application features.

## Current priorities

### Critical foundation

- fast GitHub Actions checks for pull requests;
- explicit `main` and `develop` responsibilities;
- clean and reproducible release packages;
- consistent version and tag naming;
- pull request, security, support, and conduct policies;
- automated dependency update proposals;
- removal of generated local artifacts from source exports.

### Maintainability

- test categories for unit, integration, quality, slow, Ollama, and network-dependent checks;
- centralized tooling configuration;
- gradual static analysis and typing improvements;
- documented source-authority contracts;
- documented development and release procedures;
- cleanup of merged sprint and temporary backup branches.

### Community continuity

- maintainership and governance documents;
- architecture decision records;
- component ownership when multiple maintainers exist;
- newcomer-friendly issues and contribution paths;
- release procedures that another maintainer can execute safely.

## CI philosophy

Pull request CI must be fast, local-source independent, and deterministic. Large Oracle campaigns, network integrations, and Ollama-backed evaluations remain separate manual or scheduled workflows.

A passing CI result means the selected contracts and regressions passed. It does not claim complete Magic rules coverage.

## Community ownership

Contributors should be able to determine:

- where factual authority resides;
- how the Strategist accesses sources;
- how to add a Judge tool;
- how to convert a failure into a regression;
- how to package and release the application;
- how to disclose security concerns safely.

The project should preserve these decisions in documentation and tests rather than relying on maintainer memory.
