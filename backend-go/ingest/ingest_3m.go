package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"math/rand"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/SanghunYun95/metricflow-esg/backend-go/models"
	"github.com/glebarez/sqlite"
	"github.com/joho/godotenv"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

const (
	WorkerCount      = 2     // 병렬 워커 수 축소 (SQLite 동시 쓰기 제한)
	BatchSize        = 1000  // 한 번에 Insert할 크기
	TargetCompanyCount = 50000 // 목표 기업 수 (50,000 * 60 = 3,000,000 메트릭)
)

func main() {
	start := time.Now()
	err := godotenv.Load("../.env")
	if err != nil {
		godotenv.Load(".env")
	}

	// DB 연결
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		dsn = "sqlite:///./esg_3m.db" // 3M 테스트용 파일명 명시
	}
	var dialector gorm.Dialector

	if strings.HasPrefix(dsn, "sqlite") {
		path := strings.TrimPrefix(dsn, "sqlite:///")
		dialector = sqlite.Open(path)
	} else {
		dialector = postgres.Open(dsn)
	}

	db, err := gorm.Open(dialector, &gorm.Config{
		Logger: logger.Default.LogMode(logger.Error),
	})
	if err != nil {
		log.Fatal(err)
	}

	// SQLite 성능 향상 (일회성 인제스천에 최적화된 MEMORY 모드 사용)
	sqlDB, err := db.DB()
	if err != nil {
		log.Fatal("Failed to get underlying DB connection:", err)
	}

	if strings.HasPrefix(dsn, "sqlite") || dsn == "" {
		sqlDB.SetMaxOpenConns(1)
		db.Exec("PRAGMA synchronous = OFF")
		db.Exec("PRAGMA journal_mode = MEMORY") // 인제스천 속도 최적화
	}

	// ⚠️ 주의: 기존 데이터를 삭제하고 새로 생성합니다. 
	// 프로덕션 환경이 아닌 테스트/초기 세팅 환경에서만 사용하세요.
	if err := db.Migrator().DropTable(&models.Company{}, &models.ESGMetric{}); err != nil {
		log.Fatal(err)
	}
	if err := db.AutoMigrate(&models.Company{}, &models.ESGMetric{}); err != nil {
		log.Fatal(err)
	}

	// 기존 S&P 500 데이터를 기반으로 확장 데이터 준비
	compPath := os.Getenv("COMPONENTS_CSV_PATH")
	if compPath == "" {
		compPath = "../backend/sp500_components.csv"
	}
	baseCompanies := loadBaseCompanies(compPath)
	if len(baseCompanies) == 0 {
		log.Fatal("no base companies found to expand")
	}

	// 채널 설정
	companyChan := make(chan models.Company, 200)
	var wg sync.WaitGroup

	log.Printf("Spawning %d workers to ingest 3,000,000 metrics...", WorkerCount)
	for i := 0; i < WorkerCount; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			var batch []models.Company
			for comp := range companyChan {
				batch = append(batch, comp)
				if len(batch) >= BatchSize {
					if err := db.Create(&batch).Error; err != nil {
						log.Printf("Worker %d: batch create failed: %v", workerID, err)
					} else {
						for _, c := range batch {
							generateAndSaveMetrics(db, c.ID)
						}
					}
					batch = nil
				}
			}
			// 잔여 데이터 처리
			if len(batch) > 0 {
				db.Create(&batch)
				for _, c := range batch {
					generateAndSaveMetrics(db, c.ID)
				}
			}
		}(i)
	}

	// 5만 개 기업 생성 (순차적으로 채널에 전송)
	log.Println("Expanding companies...")
	for i := 0; i < TargetCompanyCount; i++ {
		base := baseCompanies[i%len(baseCompanies)]
		suffix := i / len(baseCompanies)
		ticker := base.Ticker
		if suffix > 0 {
			ticker = fmt.Sprintf("%s_%d", base.Ticker, suffix)
		}
		
		companyChan <- models.Company{
			Ticker:       ticker,
			SecurityName: fmt.Sprintf("%s (%d)", base.SecurityName, suffix),
			Industry:     base.Industry,
		}
		
		if i > 0 && i%5000 == 0 {
			log.Printf("Pushed %d companies to pipeline...", i)
		}
	}
	close(companyChan)
	wg.Wait()

	log.Printf("Successfully ingested 3,000,000 records in %v", time.Since(start))
}

func loadBaseCompanies(path string) []models.Company {
	file, err := os.Open(path)
	if err != nil {
		log.Printf("Warning: Base company file not found at %s. Skipping expansion.", path)
		return nil
	}
	defer file.Close()

	reader := csv.NewReader(file)
	header, err := reader.Read()
	if err != nil {
		log.Printf("Failed to read CSV header: %v", err)
		return nil
	}

	hMap := make(map[string]int)
	for i, n := range header {
		hMap[n] = i
	}

	var list []models.Company
	for {
		rec, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("CSV read error: %v. Skipping record.", err)
			continue
		}

		// 헤더 인덱스 유효성 검사
		symbolIdx, hasSymbol := hMap["Symbol"]
		securityIdx, hasSecurity := hMap["Security"]
		sectorIdx, hasSector := hMap["GICS Sector"]

		if !hasSymbol || !hasSecurity || !hasSector {
			log.Printf("Missing required columns in CSV (Symbol, Security, GICS Sector). Check your CSV format.")
			return nil
		}

		list = append(list, models.Company{
			Ticker:       rec[symbolIdx],
			SecurityName: rec[securityIdx],
			Industry:     rec[sectorIdx],
		})
	}
	return list
}

func generateAndSaveMetrics(db *gorm.DB, companyID uint) {
	var metrics []models.ESGMetric
	e, s, g := 40.0+rand.Float64()*50, 40.0+rand.Float64()*50, 40.0+rand.Float64()*50
	for m := 0; m < 60; m++ {
		year := 2024 - (59-m)/12
		month := 1 + (m % 12)
		metrics = append(metrics, models.ESGMetric{
			CompanyID:       companyID,
			YearMonth:       fmt.Sprintf("%d-%02d", year, month),
			EScore:          clamp(e + rand.NormFloat64()*2),
			SScore:          clamp(s + rand.NormFloat64()*2),
			GScore:          clamp(g + rand.NormFloat64()*2),
			CarbonEmissions: 500 + rand.Float64()*5000,
		})
	}
	db.CreateInBatches(metrics, 60)
}

func clamp(v float64) float64 {
	if v < 0 { return 0 }
	if v > 100 { return 100 }
	return v
}
