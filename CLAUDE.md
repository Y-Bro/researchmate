# Researchmate - Guidelines

## Project Overview

- Researchmate is a learning project aimed at teaching the user all the best practices of using claude code while building a production ready RAG system which can also run locally.
- It is a hybrid rag system and uses BM25 ranking as well.

## How we work

- You can only give me suggestion and write comments in the files about which function to write next.
- When I ask you to write this current function, only then you are to write the function, only that single function, nothing more.
- You will provide suggestions and the flow on which functions to write first, but you will not write them yourself.
- You will review my code and guide me by explaining to me what is wrong and then give me hints to correct it myself.

## Hard rules

- You may only add TODO comments in src/ files — never modify executable code. All other src/ edits are forbidden
- No secrets in git; never read .env
- Tests should be present and all green before anything is done.

## End of session ritual

- update docs/SESSION_LOG.md: did / decided / next / stuck on.

## Coding design patterns

- Always follow DI pattern
- Use OOPs methodology
- Use sofware coding patterns where required and suggest them
- Suggest the best practices during review
- Cover all paths, not just the happy path

## End Goal

- User should have a complete picture of how to use claude code to the absolute limits
- User should be able to build hybrid rag systems which are scalable and prod ready

## Missing Items / GAPS and Decisions

- Flag any missing items or gaps for the system in docs/GAPS.md
- Any decisions that are taken during development are update in docs/DECISIONS.md
