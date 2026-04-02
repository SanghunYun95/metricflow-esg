package main

import (
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
	const endpoint = "http://localhost:9000/api/v1/esg/summary" // Python/Go 타겟 주소에 따라 수정

	fmt.Printf("Starting benchmark on %s\n", endpoint)
	fmt.Printf("Users: %d, Duration: %v\n", concurrentUsers, duration)

	start := time.Now()
	var wg sync.WaitGroup
	var mu sync.Mutex

	totalRequests := 0
	totalLatency := time.Duration(0)
	errors := 0

	stop := time.After(duration)
	
	for i := 0; i < concurrentUsers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-stop:
					return
				default:
					reqStart := time.Now()
					resp, err := http.Get(endpoint)
					latency := time.Since(reqStart)

					mu.Lock()
					totalRequests++
					if err != nil || resp.StatusCode != 200 {
						errors++
					} else {
						totalLatency += latency
						io.Copy(io.Discard, resp.Body)
						resp.Body.Close()
					}
					mu.Unlock()
				}
			}
		}()
	}

	wg.Wait()
	elapsed := time.Since(start)

	avgLatency := float64(0)
	if totalRequests > 0 {
		avgLatency = float64(totalLatency.Milliseconds()) / float64(totalRequests-errors)
	}
	rps := float64(totalRequests) / elapsed.Seconds()

	fmt.Println("\n--- Benchmark Results ---")
	fmt.Printf("Total Requests: %d\n", totalRequests)
	fmt.Printf("RPS: %.2f\n", rps)
	fmt.Printf("Avg Latency: %.2f ms\n", avgLatency)
	fmt.Printf("Errors: %d\n", errors)
}
