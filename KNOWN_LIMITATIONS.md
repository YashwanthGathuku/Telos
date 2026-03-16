# TELOS known limitations

This is a hackathon build optimized for a clear demo and a clean submission story.

## Product limits

- Windows only. The execution layer depends on Windows UI Automation.
- Desktop execution requires a live Windows session. Cloud Run cannot replace that companion.
- UI Automation coverage varies by application. Standard Windows apps work better than custom-rendered apps.
- Audio input is not enabled in the current ADK WebSocket build.
- The desktop dashboard is optional for the demo. The strongest proof path is the `POST /navigate` API plus the live desktop.

## Engineering limits

- Rust and Go native builds require a Windows machine with enough memory and paging file capacity.
- Firestore is optional and not required for the local demo.
- The repo still contains archival planning and prompt files from earlier development work; the current submission path is documented in `README.md` and `docs/`.
