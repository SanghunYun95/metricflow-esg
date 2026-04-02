package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/SanghunYun95/metricflow-esg/backend-go/models"
	"github.com/joho/godotenv"
	"gorm.io/driver/postgres"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

const (
	WorkerCount = 10   // 병렬 워커 수
	BatchSize   = 1000 // 한 번에 Insert할 크기
)

func main() {
	start := time.Now()
	err := godotenv.Load("../.env")
	if err != nil {
		godotenv.Load(".env")
	}

	// DB 연결
	dsn := os.Getenv("DATABASE_URL")
	var dialector gorm.Dialector
	if dsn == "" {
		dsn = "sqlite:///./esg_data.db"
	}

	if strings.HasPrefix(dsn, "sqlite") {
		path := strings.TrimPrefix(dsn, "sqlite:///")
		dialector = sqlite.Open(path)
	} else {
		dialector = postgres.Open(dsn)
	}

	db, err := gorm.Open(dialector, &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	})
	if err != nil {
		log.Fatal(err)
	}

	// 테이블 및 캐시 초기화
	log.Println("Invalidating existing tables and cache...")
	if err := db.Migrator().DropTable(&models.Company{}, &models.ESGMetric{}); err != nil {
		log.Fatal(fmt.Errorf("failed to drop core tables: %w", err))
	}
	
	// 캐시 아티팩트 제거 (Dialect에 따라 처리)
	dialect := db.Dialector.Name()
	if dialect == "postgres" {
		db.Exec("DROP MATERIALIZED VIEW IF EXISTS mv_esg_summary_sector")
		db.Exec("DROP MATERIALIZED VIEW IF EXISTS mv_top_companies")
	} else {
		db.Exec("DROP TABLE IF EXISTS mv_esg_summary_sector")
		db.Exec("DROP TABLE IF EXISTS mv_top_companies")
	}

	if err := db.AutoMigrate(&models.Company{}, &models.ESGMetric{}); err != nil {
		log.Fatal(fmt.Errorf("failed to auto migrate: %w", err))
	}

	// S&P 500 컴포넌트 정보 로드 (명칭, 섹터 매핑용)
	compMappingFile, err := os.Open("../backend/sp500_components.csv")
	var compNameMap = make(map[string]string)
	var compSectorMap = make(map[string]string)
	if err == nil {
		defer compMappingFile.Close()
		cReader := csv.NewReader(compMappingFile)
		cHeader, err := cReader.Read()
		if err != nil {
			log.Printf("Warning: failed to read sp500_components.csv header: %v", err)
		} else {
			cHMap := make(map[string]int)
			for i, name := range cHeader {
				cHMap[name] = i
			}
			for {
				cRec, cErr := cReader.Read()
				if cErr != nil {
					break
				}
				// 필수 컬럼 존재 여부 체크
				if symbolIdx, ok := cHMap["Symbol"]; ok {
					t := strings.TrimSpace(cRec[symbolIdx])
					if t != "" {
						if secIdx, ok := cHMap["Security"]; ok {
							compNameMap[t] = cRec[secIdx]
						}
						if sectorIdx, ok := cHMap["GICS Sector"]; ok {
							compSectorMap[t] = cRec[sectorIdx]
						}
					}
				}
			}
		}
	} else {
		log.Printf("Warning: sp500_components.csv not found, using defaults: %v", err)
	}

	rowLimit := 0
	if limitStr := os.Getenv("INGEST_ROW_LIMIT"); limitStr != "" {
		if val, err := strconv.Atoi(limitStr); err == nil {
			rowLimit = val
		}
	}

	// CSV 읽기
	file, err := os.Open("../preprocessed_content.csv")
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	header, err := reader.Read() // 헤더 스킵
	if err != nil {
		log.Fatal(err)
	}

	// 헤더 인덱스 맵핑 (정규화 및 검증)
	headerMap := make(map[string]int)
	for i, name := range header {
		// 공백 제거 및 소문자화 (BOM 등 예외 처리)
		normalized := strings.ToLower(strings.TrimSpace(name))
		headerMap[normalized] = i
	}

	tickerIdx, ok := headerMap["ticker"]
	if !ok {
		log.Fatal("missing required column: 'ticker'")
	}

	// 채널 설정 (Worker Pool 패턴)
	companyChan := make(chan models.Company, 100)
	var wg sync.WaitGroup

	log.Printf("Starting ingestion with %d workers...", WorkerCount)

	// Worker Pool 시작
	for i := 0; i < WorkerCount; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			var batch []models.Company
			for comp := range companyChan {
				batch = append(batch, comp)
				if len(batch) >= 100 { // 컴퍼니는 개수가 적으므로 작은 단위로
					if err := db.Create(&batch).Error; err != nil {
						log.Printf("insert companies failed: %v", err)
						batch = nil
						continue
					}
					// 각 컴퍼니에 대한 시뮬레이션 데이터 생성
					for _, c := range batch {
						if err := generateMetrics(db, c.ID); err != nil {
							log.Printf("insert metrics failed for company %d: %v", c.ID, err)
						}
					}
					batch = nil
				}
			}
			if len(batch) > 0 {
				if err := db.Create(&batch).Error; err != nil {
					log.Printf("insert final batch companies failed: %v", err)
				} else {
					for _, c := range batch {
						if err := generateMetrics(db, c.ID); err != nil {
							log.Printf("insert final metrics failed for company %d: %v", c.ID, err)
						}
					}
				}
			}
		}()
	}

	// 데이터 읽기 및 채널 전송
	count := 0
	seenTickers := make(map[string]bool)
	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("Warning: skipping row due to read error: %v", err)
			continue
		}

		ticker := strings.TrimSpace(record[tickerIdx])
		if ticker == "" || seenTickers[ticker] {
			continue
		}
		seenTickers[ticker] = true

		name := compNameMap[ticker]
		if name == "" {
			name = ticker + " Corp"
		}
		sector := compSectorMap[ticker]
		if sector == "" {
			sector = "Financial Services"
		}

		comp := models.Company{
			Ticker:       ticker,
			SecurityName: name,
			Industry:     sector,
		}
		companyChan <- comp
		count++

		if rowLimit > 0 && count >= rowLimit {
			break
		}
	}
	close(companyChan)
	wg.Wait()

	log.Printf("Ingestion completed! Total companies: %d", count)
	log.Printf("Time taken: %v", time.Since(start))
}

func generateMetrics(db *gorm.DB, companyID uint) error {
	var metrics []models.ESGMetric
	currentE, currentS, currentG := 50.0+rand.Float64()*40, 50.0+rand.Float64()*40, 50.0+rand.Float64()*40
	
	for i := 0; i < 60; i++ {
		year := 2024 - (59-i)/12
		month := 1 + (i % 12)
		yearMonth := fmt.Sprintf("%d-%02d", year, month)

		currentE = clamp(currentE + rand.NormFloat64())
		currentS = clamp(currentS + rand.NormFloat64())
		currentG = clamp(currentG + rand.NormFloat64())

		metrics = append(metrics, models.ESGMetric{
			CompanyID:       companyID,
			YearMonth:       yearMonth,
			EScore:          currentE,
			SScore:          currentS,
			GScore:          currentG,
			CarbonEmissions: 1000 + rand.Float64()*4000,
		})
	}
	return db.CreateInBatches(metrics, 60).Error
}

func clamp(v float64) float64 {
	if v < 0 { return 0 }
	if v > 100 { return 100 }
	return v
}
