/*
Package main — TELOS Scheduler Daemon.

HTTP service on port 8081 providing:
  - CRUD for scheduled jobs
  - Cron evaluation and trigger
  - Job execution history
  - Persistent SQLite storage

All job definitions and history are stored locally.
*/
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"regexp"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/robfig/cron/v3"
	_ "modernc.org/sqlite"
)

// ── Models ──────────────────────────────────────────────────────────────

// Job represents a scheduled task.
type Job struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	Cron      string `json:"cron"`
	Task      string `json:"task"`
	Enabled   bool   `json:"enabled"`
	CreatedAt string `json:"created_at"`
	LastRun   string `json:"last_run,omitempty"`
	NextRun   string `json:"next_run,omitempty"`
}

// JobHistory records a single execution of a job.
type JobHistory struct {
	ID        string `json:"id"`
	JobID     string `json:"job_id"`
	Status    string `json:"status"`
	Result    string `json:"result,omitempty"`
	Error     string `json:"error,omitempty"`
	StartedAt string `json:"started_at"`
	EndedAt   string `json:"ended_at,omitempty"`
}

// CreateJobRequest is the inbound payload for creating a job.
type CreateJobRequest struct {
	Name string `json:"name"`
	Cron string `json:"cron"`
	Task string `json:"task"`
}

// ── Cron Validation ─────────────────────────────────────────────────────

var cronFieldRe = regexp.MustCompile(`^(\*|\d+(-\d+)?(,\d+(-\d+)?)*)(\/\d+)?$`)

func validateCron(expr string) error {
	fields := strings.Fields(expr)
	if len(fields) != 5 {
		return fmt.Errorf("cron expression must have exactly 5 fields, got %d", len(fields))
	}
	for i, f := range fields {
		if !cronFieldRe.MatchString(f) {
			return fmt.Errorf("invalid cron field %d: %q", i+1, f)
		}
	}
	return nil
}

// ── Store ───────────────────────────────────────────────────────────────

type Store struct {
	db *sql.DB
	mu sync.RWMutex
}

func NewStore(dbPath string) (*Store, error) {
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	store := &Store{db: db}
	if err := store.configure(); err != nil {
		return nil, err
	}
	if err := store.init(); err != nil {
		return nil, err
	}
	return store, nil
}

func (s *Store) configure() error {
	_, err := s.db.Exec(`
		PRAGMA journal_mode=WAL;
		PRAGMA synchronous=NORMAL;
		PRAGMA foreign_keys=ON;
		PRAGMA busy_timeout=5000;
	`)
	return err
}

func (s *Store) init() error {
	_, err := s.db.Exec(`
		CREATE TABLE IF NOT EXISTS jobs (
			id TEXT PRIMARY KEY,
			name TEXT NOT NULL,
			cron TEXT NOT NULL,
			task TEXT NOT NULL,
			enabled INTEGER DEFAULT 1,
			created_at TEXT NOT NULL,
			last_run TEXT,
			next_run TEXT
		);
		CREATE TABLE IF NOT EXISTS job_history (
			id TEXT PRIMARY KEY,
			job_id TEXT NOT NULL,
			status TEXT NOT NULL,
			result TEXT,
			error TEXT,
			started_at TEXT NOT NULL,
			ended_at TEXT,
			FOREIGN KEY (job_id) REFERENCES jobs(id)
		);
	`)
	return err
}

func (s *Store) PingContext(ctx context.Context) error {
	return s.db.PingContext(ctx)
}

func (s *Store) CreateJob(job Job) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	_, err := s.db.Exec(
		"INSERT INTO jobs (id, name, cron, task, enabled, created_at) VALUES (?, ?, ?, ?, ?, ?)",
		job.ID, job.Name, job.Cron, job.Task, boolToInt(job.Enabled), job.CreatedAt,
	)
	return err
}

func (s *Store) ListJobs() ([]Job, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	rows, err := s.db.Query("SELECT id, name, cron, task, enabled, created_at, last_run, next_run FROM jobs ORDER BY created_at DESC")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var jobs []Job
	for rows.Next() {
		var j Job
		var enabled int
		var lastRun, nextRun sql.NullString
		if err := rows.Scan(&j.ID, &j.Name, &j.Cron, &j.Task, &enabled, &j.CreatedAt, &lastRun, &nextRun); err != nil {
			continue
		}
		j.Enabled = enabled != 0
		if lastRun.Valid {
			j.LastRun = lastRun.String
		}
		if nextRun.Valid {
			j.NextRun = nextRun.String
		}
		jobs = append(jobs, j)
	}
	return jobs, nil
}

func (s *Store) GetJob(id string) (*Job, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	var j Job
	var enabled int
	var lastRun, nextRun sql.NullString
	err := s.db.QueryRow(
		"SELECT id, name, cron, task, enabled, created_at, last_run, next_run FROM jobs WHERE id = ?", id,
	).Scan(&j.ID, &j.Name, &j.Cron, &j.Task, &enabled, &j.CreatedAt, &lastRun, &nextRun)
	if err != nil {
		return nil, err
	}
	j.Enabled = enabled != 0
	if lastRun.Valid {
		j.LastRun = lastRun.String
	}
	if nextRun.Valid {
		j.NextRun = nextRun.String
	}
	return &j, nil
}

func (s *Store) DeleteJob(id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	_, err := s.db.Exec("DELETE FROM jobs WHERE id = ?", id)
	return err
}

func (s *Store) UpdateJobRun(id string, lastRun string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	_, err := s.db.Exec("UPDATE jobs SET last_run = ? WHERE id = ?", lastRun, id)
	return err
}

func (s *Store) SaveHistory(h JobHistory) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	_, err := s.db.Exec(
		"INSERT INTO job_history (id, job_id, status, result, error, started_at, ended_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
		h.ID, h.JobID, h.Status, h.Result, h.Error, h.StartedAt, h.EndedAt,
	)
	return err
}

func (s *Store) GetHistory(jobID string, limit int) ([]JobHistory, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	rows, err := s.db.Query(
		"SELECT id, job_id, status, result, error, started_at, ended_at FROM job_history WHERE job_id = ? ORDER BY started_at DESC LIMIT ?",
		jobID, limit,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var history []JobHistory
	for rows.Next() {
		var h JobHistory
		var result, errStr, endedAt sql.NullString
		if err := rows.Scan(&h.ID, &h.JobID, &h.Status, &result, &errStr, &h.StartedAt, &endedAt); err != nil {
			continue
		}
		if result.Valid {
			h.Result = result.String
		}
		if errStr.Valid {
			h.Error = errStr.String
		}
		if endedAt.Valid {
			h.EndedAt = endedAt.String
		}
		history = append(history, h)
	}
	return history, nil
}

func (s *Store) Close() {
	s.db.Close()
}

func boolToInt(b bool) int {
	if b {
		return 1
	}
	return 0
}

// ── Middleware ───────────────────────────────────────────────────────────

// allowedOrigins for CORS (Tauri frontend + orchestrator).
var allowedOrigins = map[string]bool{
	"http://localhost:1420": true,
	"http://127.0.0.1:1420": true,
	"http://127.0.0.1:8080": true,
	"tauri://localhost":     true,
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if allowedOrigins[origin] {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Telos-Api-Token")
			w.Header().Set("Access-Control-Max-Age", "3600")
		}
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func authMiddleware(next http.Handler) http.Handler {
	requiredToken := strings.TrimSpace(os.Getenv("TELOS_API_TOKEN"))
	if requiredToken == "" {
		return next
	}

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/health", "/ready":
			next.ServeHTTP(w, r)
			return
		}

		token := extractAuthToken(r)
		if token != requiredToken {
			w.Header().Set("WWW-Authenticate", "Bearer")
			writeJSON(w, http.StatusUnauthorized, map[string]string{"error": "unauthorized"})
			return
		}
		next.ServeHTTP(w, r)
	})
}

func extractAuthToken(r *http.Request) string {
	bearer := strings.TrimSpace(r.Header.Get("Authorization"))
	if strings.HasPrefix(strings.ToLower(bearer), "bearer ") {
		return strings.TrimSpace(bearer[7:])
	}
	if token := strings.TrimSpace(r.Header.Get("X-Telos-Api-Token")); token != "" {
		return token
	}
	return strings.TrimSpace(r.URL.Query().Get("access_token"))
}

// maxBodyBytes limits POST request body size.
const maxBodyBytes = 10 * 1024 // 10 KB

// ── Route Setup (exported for testing) ──────────────────────────────────

func setupRoutes(store *Store, orchestratorURL string) http.Handler {
	mux := http.NewServeMux()

	// Health
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok", "service": "scheduler"})
	})

	mux.HandleFunc("GET /ready", func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
		defer cancel()

		if err := store.PingContext(ctx); err != nil {
			writeJSON(w, http.StatusServiceUnavailable, map[string]string{"status": "degraded", "service": "scheduler", "error": err.Error()})
			return
		}
		writeJSON(w, http.StatusOK, map[string]string{"status": "ready", "service": "scheduler"})
	})

	// List jobs
	mux.HandleFunc("GET /jobs", func(w http.ResponseWriter, r *http.Request) {
		jobs, err := store.ListJobs()
		if err != nil {
			slog.Error("failed to list jobs", "error", err)
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "internal error"})
			return
		}
		if jobs == nil {
			jobs = []Job{}
		}
		writeJSON(w, http.StatusOK, jobs)
	})

	// Create job
	mux.HandleFunc("POST /jobs", func(w http.ResponseWriter, r *http.Request) {
		r.Body = http.MaxBytesReader(w, r.Body, maxBodyBytes)
		var req CreateJobRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON or body too large"})
			return
		}
		if req.Name == "" || req.Cron == "" || req.Task == "" {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "name, cron, task are required"})
			return
		}
		if len(req.Task) > 10000 {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "task too long (max 10000)"})
			return
		}
		if err := validateCron(req.Cron); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
			return
		}

		job := Job{
			ID:        generateID(),
			Name:      req.Name,
			Cron:      req.Cron,
			Task:      req.Task,
			Enabled:   true,
			CreatedAt: time.Now().UTC().Format(time.RFC3339),
		}
		if err := store.CreateJob(job); err != nil {
			slog.Error("failed to create job", "error", err)
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "internal error"})
			return
		}
		slog.Info("job created", "id", job.ID, "name", job.Name)
		writeJSON(w, http.StatusCreated, job)
	})

	// Get job
	mux.HandleFunc("GET /jobs/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		job, err := store.GetJob(id)
		if err != nil {
			writeJSON(w, http.StatusNotFound, map[string]string{"error": "job not found"})
			return
		}
		writeJSON(w, http.StatusOK, job)
	})

	// Delete job
	mux.HandleFunc("DELETE /jobs/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		if err := store.DeleteJob(id); err != nil {
			slog.Error("failed to delete job", "id", id, "error", err)
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "internal error"})
			return
		}
		slog.Info("job deleted", "id", id)
		writeJSON(w, http.StatusOK, map[string]string{"deleted": id})
	})

	// Trigger job manually
	mux.HandleFunc("POST /jobs/{id}/trigger", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		job, err := store.GetJob(id)
		if err != nil {
			writeJSON(w, http.StatusNotFound, map[string]string{"error": "job not found"})
			return
		}

		// Forward to orchestrator
		go triggerJob(store, *job, orchestratorURL)

		slog.Info("job triggered", "id", id)
		writeJSON(w, http.StatusAccepted, map[string]string{"status": "triggered", "job_id": id})
	})

	// Job history
	mux.HandleFunc("GET /jobs/{id}/history", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		history, err := store.GetHistory(id, 50)
		if err != nil {
			slog.Error("failed to get history", "job_id", id, "error", err)
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "internal error"})
			return
		}
		if history == nil {
			history = []JobHistory{}
		}
		writeJSON(w, http.StatusOK, history)
	})

	return corsMiddleware(authMiddleware(mux))
}

// ── HTTP Handlers ───────────────────────────────────────────────────────

func main() {
	slog.SetDefault(slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo})))

	port := os.Getenv("SCHEDULER_PORT")
	if port == "" {
		port = "8081"
	}
	host := os.Getenv("SCHEDULER_HOST")
	if host == "" {
		host = "127.0.0.1"
	}

	dbPath := os.Getenv("TELOS_DB_PATH")
	if dbPath == "" {
		dbPath = "./telos_memory_db/scheduler.db"
	}

	// Ensure db directory exists
	os.MkdirAll("./telos_memory_db", 0750)

	store, err := NewStore(dbPath)
	if err != nil {
		slog.Error("failed to open database", "error", err)
		os.Exit(1)
	}
	defer store.Close()

	orchestratorURL := fmt.Sprintf("http://%s:%s",
		getenv("ORCHESTRATOR_HOST", "127.0.0.1"),
		getenv("ORCHESTRATOR_PORT", "8080"),
	)

	// Start background cron evaluator
	go runCronScheduler(store, orchestratorURL)

	handler := setupRoutes(store, orchestratorURL)

	addr := fmt.Sprintf("%s:%s", host, port)
	srv := &http.Server{
		Addr:         addr,
		Handler:      handler,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful shutdown
	done := make(chan os.Signal, 1)
	signal.Notify(done, os.Interrupt, syscall.SIGTERM)

	go func() {
		slog.Info("TELOS Scheduler starting", "addr", addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			slog.Error("server error", "error", err)
			os.Exit(1)
		}
	}()

	<-done
	slog.Info("shutdown signal received, draining connections…")

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		slog.Error("shutdown error", "error", err)
	}
	slog.Info("scheduler stopped")
}

// ── Helpers ─────────────────────────────────────────────────────────────

func triggerJob(store *Store, job Job, orchestratorURL string) {
	startedAt := time.Now().UTC().Format(time.RFC3339)
	historyID := generateID()

	client := &http.Client{Timeout: 30 * time.Second}
	body := strings.NewReader(fmt.Sprintf(`{"task": %q}`, job.Task))
	req, reqErr := http.NewRequest(http.MethodPost, orchestratorURL+"/task", body)
	if reqErr != nil {
		endedAt := time.Now().UTC().Format(time.RFC3339)
		_ = store.UpdateJobRun(job.ID, endedAt)
		_ = store.SaveHistory(JobHistory{
			ID:        historyID,
			JobID:     job.ID,
			Status:    "failed",
			Error:     reqErr.Error(),
			StartedAt: startedAt,
			EndedAt:   endedAt,
		})
		slog.Error("job trigger request build failed", "job_id", job.ID, "error", reqErr)
		return
	}
	req.Header.Set("Content-Type", "application/json")
	if token := orchestratorAuthToken(); token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	resp, err := client.Do(req)

	endedAt := time.Now().UTC().Format(time.RFC3339)
	if updateErr := store.UpdateJobRun(job.ID, endedAt); updateErr != nil {
		slog.Error("failed to update job run", "job_id", job.ID, "error", updateErr)
	}

	h := JobHistory{
		ID:        historyID,
		JobID:     job.ID,
		StartedAt: startedAt,
		EndedAt:   endedAt,
	}

	if err != nil {
		h.Status = "failed"
		h.Error = err.Error()
		slog.Error("job trigger failed", "job_id", job.ID, "error", err)
	} else {
		bodyBytes, readErr := io.ReadAll(resp.Body)
		resp.Body.Close()
		if resp.StatusCode < 300 {
			h.Result = string(bodyBytes)
			if readErr != nil {
				h.Status = "failed"
				h.Error = fmt.Sprintf("failed to read orchestrator response: %v", readErr)
				slog.Warn("job returned unreadable body", "job_id", job.ID, "error", readErr)
			} else {
				var taskResp struct {
					Status string `json:"status"`
					Error  string `json:"error"`
				}
				if err := json.Unmarshal(bodyBytes, &taskResp); err == nil && taskResp.Status != "" {
					if taskResp.Status == "completed" {
						h.Status = "completed"
						slog.Info("job completed", "job_id", job.ID, "http_status", resp.StatusCode)
					} else {
						h.Status = "failed"
						if taskResp.Error != "" {
							h.Error = taskResp.Error
						} else {
							h.Error = fmt.Sprintf("task status %s", taskResp.Status)
						}
						slog.Warn("job completed HTTP request but task failed", "job_id", job.ID, "task_status", taskResp.Status)
					}
				} else {
					h.Status = "failed"
					h.Error = "orchestrator response missing task status"
					slog.Warn("job completed HTTP request but response had no task status", "job_id", job.ID)
				}
			}
		} else {
			h.Status = "failed"
			h.Error = fmt.Sprintf("HTTP %d", resp.StatusCode)
			slog.Warn("job returned error", "job_id", job.ID, "http_status", resp.StatusCode)
		}
	}

	if saveErr := store.SaveHistory(h); saveErr != nil {
		slog.Error("failed to save history", "history_id", historyID, "error", saveErr)
	}
}

func orchestratorAuthToken() string {
	for _, key := range []string{"TELOS_INTERNAL_TOKEN", "ORCHESTRATOR_API_TOKEN", "TELOS_API_TOKEN"} {
		if value := strings.TrimSpace(os.Getenv(key)); value != "" {
			return value
		}
	}
	return ""
}

func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func generateID() string {
	return fmt.Sprintf("%x", time.Now().UnixNano())
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

// runCronScheduler polls the database every minute and triggers jobs if their cron schedule elapsed.
func runCronScheduler(store *Store, orchestratorURL string) {
	slog.Info("Starting background cron scheduler loop")
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	// Ensure we parse standard cron
	parser := cron.NewParser(cron.Minute | cron.Hour | cron.Dom | cron.Month | cron.Dow | cron.Descriptor)

	for range ticker.C {
		jobs, err := store.ListJobs()
		if err != nil {
			slog.Error("cron scheduler: failed to list jobs", "error", err)
			continue
		}

		now := time.Now().UTC()
		for _, job := range jobs {
			if !job.Enabled {
				continue
			}

			schedule, err := parser.Parse(job.Cron)
			if err != nil {
				slog.Warn("cron scheduler: invalid script cron", "job", job.ID, "cron", job.Cron, "error", err)
				continue
			}

			// If never run, set last run to creation time, else parse last run
			var last time.Time
			if job.LastRun == "" {
				last, _ = time.Parse(time.RFC3339, job.CreatedAt)
			} else {
				last, _ = time.Parse(time.RFC3339, job.LastRun)
			}

			next := schedule.Next(last)
			if now.After(next) || now.Equal(next) {
				slog.Info("cron scheduler: triggering scheduled job", "job", job.ID, "name", job.Name)
				go triggerJob(store, job, orchestratorURL)
			}
		}
	}
}
