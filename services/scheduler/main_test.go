package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

// ── Cron Validation Tests ───────────────────────────────────────────────

func TestValidateCron_Valid(t *testing.T) {
	valid := []string{
		"* * * * *",
		"0 9 * * 1",
		"*/5 * * * *",
		"0 0 1 1 *",
		"30 4 1-7 * 5",
		"0,15,30,45 * * * *",
	}
	for _, expr := range valid {
		if err := validateCron(expr); err != nil {
			t.Errorf("validateCron(%q) unexpected error: %v", expr, err)
		}
	}
}

func TestValidateCron_Invalid(t *testing.T) {
	invalid := []string{
		"",
		"* * *",
		"* * * * * *",
		"abc * * * *",
		"* * * * MON",
	}
	for _, expr := range invalid {
		if err := validateCron(expr); err == nil {
			t.Errorf("validateCron(%q) expected error, got nil", expr)
		}
	}
}

// ── Store Tests ─────────────────────────────────────────────────────────

func newTestStore(t *testing.T) *Store {
	t.Helper()
	tmpFile, err := os.CreateTemp("", "scheduler_test_*.db")
	if err != nil {
		t.Fatal(err)
	}
	tmpFile.Close()
	t.Cleanup(func() { os.Remove(tmpFile.Name()) })

	store, err := NewStore(tmpFile.Name())
	if err != nil {
		t.Fatalf("NewStore: %v", err)
	}
	t.Cleanup(func() { store.Close() })
	return store
}

func TestStoreCreateAndGetJob(t *testing.T) {
	store := newTestStore(t)

	job := Job{
		ID: "test-1", Name: "backup", Cron: "0 2 * * *",
		Task: "run backup", Enabled: true, CreatedAt: "2025-01-01T00:00:00Z",
	}
	if err := store.CreateJob(job); err != nil {
		t.Fatalf("CreateJob: %v", err)
	}

	got, err := store.GetJob("test-1")
	if err != nil {
		t.Fatalf("GetJob: %v", err)
	}
	if got.Name != "backup" || got.Cron != "0 2 * * *" || !got.Enabled {
		t.Errorf("unexpected job: %+v", got)
	}
}

func TestStoreListJobs(t *testing.T) {
	store := newTestStore(t)

	for i := range 3 {
		store.CreateJob(Job{
			ID: generateID() + string(rune('a'+i)), Name: "job",
			Cron: "* * * * *", Task: "task", Enabled: true, CreatedAt: "2025-01-01T00:00:00Z",
		})
	}
	jobs, err := store.ListJobs()
	if err != nil {
		t.Fatalf("ListJobs: %v", err)
	}
	if len(jobs) != 3 {
		t.Errorf("expected 3 jobs, got %d", len(jobs))
	}
}

func TestStoreDeleteJob(t *testing.T) {
	store := newTestStore(t)
	store.CreateJob(Job{
		ID: "del-1", Name: "x", Cron: "* * * * *",
		Task: "t", Enabled: true, CreatedAt: "2025-01-01T00:00:00Z",
	})

	if err := store.DeleteJob("del-1"); err != nil {
		t.Fatalf("DeleteJob: %v", err)
	}
	if _, err := store.GetJob("del-1"); err == nil {
		t.Error("expected error after delete, got nil")
	}
}

func TestStoreHistory(t *testing.T) {
	store := newTestStore(t)
	if err := store.CreateJob(Job{
		ID: "j-1", Name: "history", Cron: "* * * * *",
		Task: "record history", Enabled: true, CreatedAt: "2025-01-01T00:00:00Z",
	}); err != nil {
		t.Fatalf("CreateJob: %v", err)
	}
	h := JobHistory{
		ID: "h-1", JobID: "j-1", Status: "completed",
		Result: "ok", StartedAt: "2025-01-01T00:00:00Z", EndedAt: "2025-01-01T00:01:00Z",
	}
	if err := store.SaveHistory(h); err != nil {
		t.Fatalf("SaveHistory: %v", err)
	}
	history, err := store.GetHistory("j-1", 10)
	if err != nil {
		t.Fatalf("GetHistory: %v", err)
	}
	if len(history) != 1 || history[0].Status != "completed" {
		t.Errorf("unexpected history: %+v", history)
	}
}

func TestStoreGetJob_NotFound(t *testing.T) {
	store := newTestStore(t)
	if _, err := store.GetJob("nonexistent"); err == nil {
		t.Error("expected error for nonexistent job, got nil")
	}
}

// ── HTTP Handler Tests ──────────────────────────────────────────────────

func testServer(t *testing.T) (*Store, *httptest.Server) {
	t.Helper()
	store := newTestStore(t)
	handler := setupRoutes(store, "http://127.0.0.1:9999")
	ts := httptest.NewServer(handler)
	t.Cleanup(ts.Close)
	return store, ts
}

func TestHealthEndpoint(t *testing.T) {
	_, ts := testServer(t)
	resp, err := http.Get(ts.URL + "/health")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("expected 200, got %d", resp.StatusCode)
	}
	var body map[string]string
	json.NewDecoder(resp.Body).Decode(&body)
	if body["status"] != "ok" {
		t.Errorf("expected status ok, got %q", body["status"])
	}
}

func TestReadyEndpoint(t *testing.T) {
	_, ts := testServer(t)
	resp, err := http.Get(ts.URL + "/ready")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
}

func TestCreateAndListJobs(t *testing.T) {
	_, ts := testServer(t)

	// Create
	payload := `{"name":"test","cron":"*/5 * * * *","task":"do thing"}`
	resp, err := http.Post(ts.URL+"/jobs", "application/json", strings.NewReader(payload))
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("expected 201, got %d", resp.StatusCode)
	}
	var created Job
	json.NewDecoder(resp.Body).Decode(&created)
	if created.Name != "test" {
		t.Errorf("expected name 'test', got %q", created.Name)
	}

	// List
	resp2, _ := http.Get(ts.URL + "/jobs")
	defer resp2.Body.Close()
	var jobs []Job
	json.NewDecoder(resp2.Body).Decode(&jobs)
	if len(jobs) != 1 {
		t.Errorf("expected 1 job, got %d", len(jobs))
	}
}

func TestCreateJob_InvalidCron(t *testing.T) {
	_, ts := testServer(t)
	payload := `{"name":"bad","cron":"not valid","task":"do thing"}`
	resp, err := http.Post(ts.URL+"/jobs", "application/json", strings.NewReader(payload))
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", resp.StatusCode)
	}
}

func TestCreateJob_MissingFields(t *testing.T) {
	_, ts := testServer(t)
	payload := `{"name":"only name"}`
	resp, err := http.Post(ts.URL+"/jobs", "application/json", strings.NewReader(payload))
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", resp.StatusCode)
	}
}

func TestCreateJob_InvalidJSON(t *testing.T) {
	_, ts := testServer(t)
	resp, err := http.Post(ts.URL+"/jobs", "application/json", strings.NewReader("{bad"))
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", resp.StatusCode)
	}
}

func TestGetJob_NotFound(t *testing.T) {
	_, ts := testServer(t)
	resp, err := http.Get(ts.URL + "/jobs/nonexistent")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNotFound {
		t.Errorf("expected 404, got %d", resp.StatusCode)
	}
}

func TestDeleteJob(t *testing.T) {
	store, ts := testServer(t)
	store.CreateJob(Job{
		ID: "del-http", Name: "x", Cron: "* * * * *",
		Task: "t", Enabled: true, CreatedAt: "2025-01-01T00:00:00Z",
	})

	req, _ := http.NewRequest(http.MethodDelete, ts.URL+"/jobs/del-http", nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("expected 200, got %d", resp.StatusCode)
	}
}

func TestTriggerJob_NotFound(t *testing.T) {
	_, ts := testServer(t)
	resp, err := http.Post(ts.URL+"/jobs/nonexistent/trigger", "", nil)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNotFound {
		t.Errorf("expected 404, got %d", resp.StatusCode)
	}
}

func TestJobHistory_Empty(t *testing.T) {
	_, ts := testServer(t)
	resp, err := http.Get(ts.URL + "/jobs/any-id/history")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("expected 200, got %d", resp.StatusCode)
	}
	var history []JobHistory
	json.NewDecoder(resp.Body).Decode(&history)
	if len(history) != 0 {
		t.Errorf("expected empty history, got %d entries", len(history))
	}
}

func TestTriggerJob_PersistsFailedTaskStatus(t *testing.T) {
	store := newTestStore(t)
	job := Job{
		ID: "job-1", Name: "sync", Cron: "* * * * *",
		Task: "do thing", Enabled: true, CreatedAt: "2025-01-01T00:00:00Z",
	}
	if err := store.CreateJob(job); err != nil {
		t.Fatalf("CreateJob: %v", err)
	}

	orchestrator := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"task_id":"t1","status":"failed","error":"provider offline"}`))
	}))
	defer orchestrator.Close()

	triggerJob(store, job, orchestrator.URL)

	history, err := store.GetHistory(job.ID, 10)
	if err != nil {
		t.Fatalf("GetHistory: %v", err)
	}
	if len(history) != 1 {
		t.Fatalf("expected 1 history entry, got %d", len(history))
	}
	if history[0].Status != "failed" {
		t.Fatalf("expected failed history entry, got %q", history[0].Status)
	}
	if !strings.Contains(history[0].Error, "provider offline") {
		t.Fatalf("expected orchestrator error to be preserved, got %q", history[0].Error)
	}
}

func TestAuthMiddleware_RejectsUnauthorizedRequests(t *testing.T) {
	t.Setenv("TELOS_API_TOKEN", "secret-token")
	_, ts := testServer(t)

	resp, err := http.Get(ts.URL + "/jobs")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", resp.StatusCode)
	}
}

func TestAuthMiddleware_AcceptsBearerToken(t *testing.T) {
	t.Setenv("TELOS_API_TOKEN", "secret-token")
	_, ts := testServer(t)

	req, _ := http.NewRequest(http.MethodGet, ts.URL+"/jobs", nil)
	req.Header.Set("Authorization", "Bearer secret-token")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
}

func TestTriggerJob_ForwardsInternalToken(t *testing.T) {
	t.Setenv("TELOS_INTERNAL_TOKEN", "internal-token")
	store := newTestStore(t)
	job := Job{
		ID: "job-2", Name: "sync", Cron: "* * * * *",
		Task: "do thing", Enabled: true, CreatedAt: "2025-01-01T00:00:00Z",
	}
	if err := store.CreateJob(job); err != nil {
		t.Fatalf("CreateJob: %v", err)
	}

	var authHeader string
	orchestrator := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader = r.Header.Get("Authorization")
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"task_id":"t1","status":"completed"}`))
	}))
	defer orchestrator.Close()

	triggerJob(store, job, orchestrator.URL)

	if authHeader != "Bearer internal-token" {
		t.Fatalf("expected internal token to be forwarded, got %q", authHeader)
	}
}

// ── CORS Tests ──────────────────────────────────────────────────────────

func TestCORS_AllowedOrigin(t *testing.T) {
	_, ts := testServer(t)
	req, _ := http.NewRequest(http.MethodGet, ts.URL+"/health", nil)
	req.Header.Set("Origin", "http://localhost:1420")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if got := resp.Header.Get("Access-Control-Allow-Origin"); got != "http://localhost:1420" {
		t.Errorf("expected CORS origin header, got %q", got)
	}
}

func TestCORS_DisallowedOrigin(t *testing.T) {
	_, ts := testServer(t)
	req, _ := http.NewRequest(http.MethodGet, ts.URL+"/health", nil)
	req.Header.Set("Origin", "http://evil.com")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if got := resp.Header.Get("Access-Control-Allow-Origin"); got != "" {
		t.Errorf("expected no CORS header for disallowed origin, got %q", got)
	}
}

func TestCORS_Preflight(t *testing.T) {
	_, ts := testServer(t)
	req, _ := http.NewRequest(http.MethodOptions, ts.URL+"/jobs", nil)
	req.Header.Set("Origin", "http://localhost:1420")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNoContent {
		t.Errorf("expected 204 for preflight, got %d", resp.StatusCode)
	}
}
