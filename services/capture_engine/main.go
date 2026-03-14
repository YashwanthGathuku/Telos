package main

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"image/png"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/kbinani/screenshot"
)

type CaptureResponse struct {
	Image string `json:"image"`
}

type ErrorResponse struct {
	Error string `json:"error"`
}

func main() {
	port := os.Getenv("CAPTURE_ENGINE_PORT")
	if port == "" {
		port = "8084"
	}
	host := os.Getenv("CAPTURE_ENGINE_HOST")
	if host == "" {
		host = "127.0.0.1"
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", healthHandler)
	mux.HandleFunc("/ready", readyHandler)
	mux.HandleFunc("/capture/screen", captureScreenHandler)
	mux.HandleFunc("/delta", deltaHandler) // Placeholder for delta engine API

	addr := fmt.Sprintf("%s:%s", host, port)
	log.Printf("Starting Go Capture Engine on %s\n", addr)
	server := &http.Server{
		Addr:         addr,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}
	if err := server.ListenAndServe(); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok", "service": "capture_engine"})
}

func readyHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if screenshot.NumActiveDisplays() <= 0 {
		sendError(w, "Active display not found", http.StatusServiceUnavailable)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ready", "service": "capture_engine"})
}

func captureScreenHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Capture the primary display (display index 0)
	n := screenshot.NumActiveDisplays()
	if n <= 0 {
		sendError(w, "Active display not found", http.StatusInternalServerError)
		return
	}

	bounds := screenshot.GetDisplayBounds(0)
	img, err := screenshot.CaptureRect(bounds)
	if err != nil {
		sendError(w, fmt.Sprintf("failed to capture screen: %v", err), http.StatusInternalServerError)
		return
	}

	// Encode to PNG
	var buf bytes.Buffer
	if err := png.Encode(&buf, img); err != nil {
		sendError(w, fmt.Sprintf("failed to encode PNG: %v", err), http.StatusInternalServerError)
		return
	}

	// Convert bytes to base64
	b64Image := base64.StdEncoding.EncodeToString(buf.Bytes())

	// Send JSON response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(CaptureResponse{Image: b64Image})
}

// Dummy endpoint matching the Rust delta phase 2c requirements
func deltaHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"changes": []}`))
}

func sendError(w http.ResponseWriter, msg string, code int) {
	log.Printf("Error: %s", msg)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(ErrorResponse{Error: msg})
}
