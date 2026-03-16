# TELOS architecture diagram

```mermaid
flowchart LR
    User["User"] --> API["FastAPI + ADK Navigator"]
    API --> Gemini["Gemini 2.0 Flash"]
    API --> Firestore["Firestore (optional)"]
    API --> Companion["Windows companion host"]
    Companion --> UIGraph["UIGraph :8083"]
    Companion --> Capture["Screenshot engine :8085"]
    UIGraph --> Desktop["Windows desktop apps"]
    Capture --> Desktop
```

## Reading the diagram

- The FastAPI service is the Gemini orchestration layer.
- Gemini reasons over screenshot input and chooses tools.
- The Windows companion executes the UI actions and produces screenshots.
- Firestore is optional for cloud-backed memory when deployed on Google Cloud.
