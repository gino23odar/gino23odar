# GINO.OS · Command Reference

```text
G I N O . O S  /  G I T H U B   E D I T I O N

visitor@github:~$ help

Available commands:
  whoami         professional profile
  experience     backend and QA engineering
  projects       featured public repositories
  stack          backend, data, delivery and QA tools
  ai             AI tooling and current learning areas
  architecture   conceptual AI systems diagram
  contact        public professional links
  ask            public Q&A through GitHub Issues
```

## Expand a command

| Command | Expanded content |
| :-- | :-- |
| [`whoami`](../../README.md#gino-whoami) | Professional overview |
| [`experience`](../../README.md#gino-experience) | Engineering experience and Playwright QA |
| [`projects`](../../README.md#gino-projects) | Hot-swappable project gallery |
| [`stack`](../../README.md#gino-stack) | Backend, data, CI/CD, observability and QA |
| [`ai`](../../README.md#gino-ai) | AI tooling and learning areas |
| [`architecture`](../../README.md#gino-architecture) | AI reference architecture |
| [`contact`](../../README.md#gino-contact) | Portfolio, GitHub and LinkedIn |
| [`ask`](../../README.md#gino-ask) | Open the panel, then select the public question form |

GitHub supports native `<details>` panels. Clicking a command expands its content below the command card; clicking again collapses it. Several sections can be open simultaneously. No JavaScript runs in the README.

## Asking a custom question

1. Open the [`ask` panel](../../README.md#gino-ask) and select **Open the GINO.OS question form**.
2. Complete the public GitHub Issue form and submit it while signed in to GitHub.
3. The GINO.OS Action posts a **knowledge-base answer** in the Issue thread. This works without a paid AI API.
4. To continue the thread, comment `/ask What about Playwright and regression testing?` (up to three follow-ups).

**Important:** This interaction uses GitHub Issues, not an editable text field inside the README. Questions and answers are public. Answers are grounded in `config/profile_knowledge.json` and the featured entries in `config/projects.json`. AI-powered phrasing is optional and is disabled unless the repo owner configures it explicitly.

[← Back to GitHub profile](../../README.md#ginoos)
