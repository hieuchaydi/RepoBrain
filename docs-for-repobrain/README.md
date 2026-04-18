# RepoBrain Docs Frontend

This app is a human-friendly documentation frontend for the RepoBrain repository.

It is meant to help new contributors, reviewers, and demo audiences understand:

- what RepoBrain does
- which commands matter most
- where the important docs live
- what is already validated locally
- what still depends on remote workflow access or real provider credentials

## Run Locally

```bash
cd docs-for-repobrain
npm install
npm run dev
```

Then open the Vite URL shown in the terminal.

## Build

```bash
npm run build
npm run lint
```

## Main Features

- modern light/dark docs UI
- RepoBrain logo and brand styling based on the project artwork
- searchable command catalog
- searchable docs library
- embedded markdown reading room sourced from the real repo docs
- release-state summary for what is done locally versus what still needs remote validation
