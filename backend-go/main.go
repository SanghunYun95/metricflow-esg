package main

import (
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/SanghunYun95/metricflow-esg/backend-go/models"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"gorm.io/driver/postgres"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var db *gorm.DB

func initDB() {
	err := godotenv.Load("../.env")
	if err != nil {
		log.Println("Error loading .env file from root, checking current dir...")
		godotenv.Load(".env")
	}

	dsn := os.Getenv("DATABASE_URL")
	var dialector gorm.Dialector

	if dsn == "" || strings.HasPrefix(dsn, "sqlite") {
		if dsn == "" {
			dsn = "sqlite:///./esg_data.db"
		}
		// Clean up sqlite prefix for GORM
		path := strings.TrimPrefix(dsn, "sqlite:///")
		dialector = sqlite.Open(path)
	} else {
		dialector = postgres.Open(dsn)
	}

	newLogger := logger.New(
		log.New(os.Stdout, "\r\n", log.LstdFlags),
		logger.Config{
			SlowThreshold:             time.Second,
			LogLevel:                  logger.Info,
			IgnoreRecordNotFoundError: true,
			Colorful:                  true,
		},
	)

	database, err := gorm.Open(dialector, &gorm.Config{
		Logger: newLogger,
	})
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}

	db = database
	log.Println("Database connection established")
}

func main() {
	initDB()

	r := gin.Default()

	// CORS Setup
	r.Use(func(c *gin.Context) {
		origin := c.Request.Header.Get("Origin")
		if origin != "" {
			c.Writer.Header().Set("Access-Control-Allow-Origin", origin)
			c.Writer.Header().Set("Vary", "Origin")
		} else {
			c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		}
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT, DELETE")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	})

	api := r.Group("/api/v1")
	{
		api.GET("/sectors", getSectors)
		api.GET("/esg/summary", getESGSummary)
		api.GET("/esg/top-companies", getTopCompanies)
		api.POST("/system/refresh-cache", refreshCache)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Server starting on port %s", port)
	r.Run(":" + port)
}

func getSectors(c *gin.Context) {
	var sectors []string
	result := db.Model(&models.Company{}).
		Distinct("industry").
		Where("industry IS NOT NULL AND industry != 'Unknown'").
		Pluck("industry", &sectors)

	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
		return
	}

	c.JSON(http.StatusOK, sectors)
}

func getESGSummary(c *gin.Context) {
	sector := c.Query("sector")
	var summary []models.SectorSummary

	query := db.Table("mv_esg_summary_sector")
	if sector != "" {
		query = query.Where("sector = ?", sector)
	}

	err := query.Find(&summary).Error
	if err != nil {
		log.Println("Cache miss or error, falling back to manual aggregation:", err)
		// Fallback logic
		manualQuery := db.Table("companies").
			Select("companies.industry as sector, AVG(esg_metrics.e_score) as avg_e_score, AVG(esg_metrics.s_score) as avg_s_score, AVG(esg_metrics.g_score) as avg_g_score, AVG((esg_metrics.e_score + esg_metrics.s_score + esg_metrics.g_score) / 3.0) as avg_total_score").
			Joins("JOIN esg_metrics ON companies.id = esg_metrics.company_id").
			Group("companies.industry").
			Where("companies.industry IS NOT NULL AND companies.industry != 'Unknown'")

		if sector != "" {
			manualQuery = manualQuery.Where("companies.industry = ?", sector)
		}

		if err := manualQuery.Scan(&summary).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
	}

	c.JSON(http.StatusOK, summary)
}

func getTopCompanies(c *gin.Context) {
	sector := c.Query("sector")
	var topCompanies []models.TopCompany

	query := db.Table("mv_top_companies")
	if sector != "" {
		query = query.Where("sector = ?", sector)
	}

	err := query.Order("total_score DESC").Limit(10).Find(&topCompanies).Error
	if err != nil {
		log.Println("Cache miss or error, falling back to manual aggregation:", err)
		manualQuery := db.Table("companies").
			Select("companies.ticker, companies.security_name, AVG(esg_metrics.e_score) as e_score, AVG(esg_metrics.s_score) as s_score, AVG(esg_metrics.g_score) as g_score, AVG((esg_metrics.e_score + esg_metrics.s_score + esg_metrics.g_score) / 3.0) as total_score").
			Joins("JOIN esg_metrics ON companies.id = esg_metrics.company_id").
			Group("companies.ticker, companies.security_name")

		if sector != "" {
			manualQuery = manualQuery.Where("companies.industry = ?", sector)
		}

		if err := manualQuery.Order("total_score DESC").Limit(10).Scan(&topCompanies).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
	}

	c.JSON(http.StatusOK, topCompanies)
}

func refreshCache(c *gin.Context) {
	// Go의 강점: 고루틴을 활용한 논블로킹 백그라운드 처리
	go func() {
		log.Println("Background cache refresh started...")
		// Materialized View 갱신 로직 (Postgres 기준)
		dialect := db.Dialector.Name()
		if dialect == "postgres" {
			// REFRESH MATERIALIZED VIEW 실행 (동시성 확보를 위해 CONCURRENTLY 사용 권장이나 초기엔 아닐 수 있으므로 일반 실행 병행)
			if err := db.Exec("REFRESH MATERIALIZED VIEW mv_esg_summary_sector").Error; err != nil {
				log.Printf("Error refreshing mv_esg_summary_sector: %v", err)
			}
			if err := db.Exec("REFRESH MATERIALIZED VIEW mv_top_companies").Error; err != nil {
				log.Printf("Error refreshing mv_top_companies: %v", err)
			}
		} else {
			// SQLite 등에서는 View나 캐시 테이블 재구조화 로직 필요 (여기선 로그만)
			time.Sleep(1 * time.Second)
			log.Println("Background cache refresh simulated for non-postgres dialect.")
		}
		log.Println("Background cache refresh completed.")
	}()

	c.JSON(http.StatusAccepted, gin.H{
		"status":  "accepted",
		"message": "Cache refresh started in the background (Goroutine)",
	})
}
