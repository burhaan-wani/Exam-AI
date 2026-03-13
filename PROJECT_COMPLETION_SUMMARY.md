# Project Summary

This file is retained as a lightweight historical summary only.

The live source of truth for the current system is:
- `README.md`
- `API_REFERENCE.md`
- `FEATURES.md`

## Current state of the application
- The legacy teacher blueprint/HITL pipeline has been removed from the codebase.
- The teacher workflow now runs through syllabus upload, reference upload, question-bank generation, paper generation, and final paper review.
- Backend JWT auth and role-based access checks are enforced.
- Retrieval now uses a persistent Chroma-backed vector store per syllabus.
- Frontend PDF export is implemented.

## Important note
Older descriptions of blueprint creation, HITL review modules, or direct OpenAI GPT-4 usage no longer describe the live implementation.
Use the current docs listed above when working on the project.
