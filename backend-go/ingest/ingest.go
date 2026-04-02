package main

import (
	"encoding/csv"
	"io"
	"log"
	"math/rand"
	"os"
	"strconv"
	"sync"
	"time"

	"github.com/SanghunYun95/metricflow-esg/backend-go/models"
	"github.com/joho/godotenv"
	"github.com/schollz/progressbar/v3"
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
	if dsn == "" || dsn == "sqlite:///./esg_data.db" {
		dialector = sqlite.Open("./esg_data.db")
	} else {
		dialector = postgres.Open(dsn)
	}

	db, err := gorm.Open(dialector, &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	})
	if err != nil {
		log.Fatal(err)
	}

	// 테이블 초기화 (테스트용이므로 매번 초기화)
	db.Migrator().DropTable(&models.Company{}, &models.ESGMetric{})
	db.AutoMigrate(&models.Company{}, &models.ESGMetric{})

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

	// 헤더 인덱스 맵핑
	headerMap := make(map[string]int)
	for i, name := range header {
		headerMap[name] = i
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
					db.Create(&batch)
					// 각 컴퍼니에 대한 시뮬레이션 데이터 생성
					for _, c := range batch {
						generateMetrics(db, c.ID)
					}
					batch = nil
				}
			}
			if len(batch) > 0 {
				db.Create(&batch)
				for _, c := range batch {
					generateMetrics(db, c.ID)
				}
			}
		}()
	}

	// 데이터 읽기 및 채널 전송
	count := 0
	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}

		ticker := record[headerMap["ticker"]]
		comp := models.Company{
			Ticker:       ticker,
			SecurityName: ticker + " Corp", // 실제 데이터에서는 sp500_components.csv와 조인 필요
			Industry:     "Financial Services", // 임시 섹터
		}
		companyChan <- comp
		count++
		
		if count >= 100 { // 테스트를 위해 100개사만 진행 (실제로는 제한 없음)
			break
		}
	}
	close(companyChan)
	wg.Wait()

	log.Printf("Ingestion completed! Total companies: %d", count)
	log.Printf("Time taken: %v", time.Since(start))
}

func generateMetrics(db *gorm.DB, companyID uint) {
	var metrics []models.ESGMetric
	currentE, currentS, currentG := 50.0+rand.Float64()*40, 50.0+rand.Float64()*40, 50.0+rand.Float64()*40
	
	for i := 0; i < 60; i++ {
		year := 2024 - (59-i)/12
		month := 1 + (i % 12)
		yearMonth := strconv.Itoa(year) + "-" + strconv.FormatInt(int64(month), 10)
		if month < 10 {
			yearMonth = strconv.Itoa(year) + "-0" + strconv.FormatInt(int64(month), 10)
		}

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
	db.CreateInBatches(metrics, 60)
}

func clamp(v float64) float64 {
	if v < 0 { return 0 }
	if v > 100 { return 100 }
	return v
}
