# TELOS submission runbook

Use this on submission day.

## 1. Push the cleaned repo

- Commit the Gemini-only cleanup
- Push to the public GitHub repo
- Open the public repo in a browser and verify the README is the Gemini version

## 2. Verify the local demo

- Start UIGraph
- Start the screenshot engine
- Start the orchestrator
- Confirm `/health` and `/adk/health`
- Run one `POST /navigate` command successfully

## 3. Verify the cloud deployment

- Confirm Cloud Run is deployed
- Confirm `/health` works on the Cloud Run URL
- Confirm the Google Cloud services you used are visible: Cloud Run, Secret Manager, and Firestore

## 4. Record the demo

- Follow `docs/demo/HERO_DEMO.md`
- Keep it under 4 minutes
- Upload it as a public video

## 5. Fill Devpost

- Title and tagline from `docs/devpost_submission.md`
- Description from `docs/devpost_submission.md`
- Public GitHub repo URL
- Public video URL
- Category: `UI Navigator`

## 6. Final checks

- README matches the video
- Submission copy is consistent with the Gemini and Google Cloud implementation
- The repo shows Gemini, ADK, and Google Cloud clearly
- The demo video shows real desktop actions and cloud evidence
