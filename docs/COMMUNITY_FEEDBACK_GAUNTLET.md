# Community Feedback Gauntlet

This workflow accepts manually curated and preferably paraphrased real-world questions. It is an evaluation workflow, not training data ingestion.

## Safety rules

- Do not scrape forums.
- Do not copy large copyrighted discussions.
- Do not treat community answers as rules authority.
- Revalidate every promoted case against current Oracle, Comprehensive Rules, and rulings.
- Do not promote cases automatically.

## Workflow

1. Export an exploratory case from the local UI.
2. Add reviewer notes and expected behavior.
3. Execute the exploratory campaign.
4. Inspect failures and evidence.
5. Manually validate the case against current sources.
6. Promote only reviewed cases into regression coverage.

Artifacts explicitly contain:

```json
{
  "artifact_purpose": "evaluation",
  "training_allowed": false,
  "automatic_learning": false,
  "automatic_promotion": false
}
```
