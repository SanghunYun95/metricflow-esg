package main

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"
)

func main() {
	// 50명의 동시 사용자가 10초간 요청
	const concurrentUsers = 50
	const duration = 10 * time.Second
	const endpoint = "http://localhost:8080/api/v1/esg/summary" // Go 서버 포트인 8080으로 수정

	fmt.Printf("Starting benchmark on %s\n", endpoint)
	fmt.Printf("Users: %d, Duration: %v\n", concurrentUsers, duration)

	start := time.Now()
	var wg sync.WaitGroup
	var mu sync.Mutex

	totalRequests := 0
	totalLatency := time.Duration(0)
	successfulRequests := 0
	errors := 0

	ctx, cancel := context.WithTimeout(context.Background(), duration)
	defer cancel()

	client := &http.Client{
		Timeout: 5 * time.Second,
	}
	
	for i := 0; i < concurrentUsers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				default:
					reqStart := time.Now()
					resp, err := client.Get(endpoint)
					latency := time.Since(reqStart)

					if resp != nil {
						io.Copy(io.Discard, resp.Body)
						resp.Body.Close()
					}

					mu.Lock()
					totalRequests++
					if err != nil || resp == nil || resp.StatusCode != 200 {
						errors++
					} else {
						successfulRequests++
						totalLatency += latency
					}
					mu.Unlock()
				}
			}
		}()
	}

	wg.Wait()
	elapsed := time.Since(start)

	avgLatency := float64(0)
	if successfulRequests > 0 {
		avgLatency = float64(totalLatency.Milliseconds()) / float64(successfulRequests)
	}
	rps := float64(totalRequests) / elapsed.Seconds()

	fmt.Println("\n--- Benchmark Results ---")
	fmt.Printf("Total Requests: %d\n", totalRequests)
	fmt.Printf("RPS: %.2f\n", rps)
	fmt.Printf("Avg Latency: %.2f ms\n", avgLatency)
	fmt.Printf("Errors: %d\n", errors)
}
