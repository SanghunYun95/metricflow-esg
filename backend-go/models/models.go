package models

// Company represents the companies table
type Company struct {
	ID           uint        `gorm:"primaryKey" json:"id"`
	Ticker       string      `gorm:"uniqueIndex;not null" json:"ticker"`
	SecurityName string      `json:"security_name"`
	Industry     string      `gorm:"index" json:"industry"` // GICS Sector
	ESGMetrics   []ESGMetric `gorm:"foreignKey:CompanyID" json:"esg_metrics"`
}

// ESGMetric represents the esg_metrics table
type ESGMetric struct {
	ID             uint    `gorm:"primaryKey" json:"id"`
	CompanyID      uint    `gorm:"index;not null" json:"company_id"`
	YearMonth      string  `gorm:"not null" json:"year_month"` // YYYY-MM
	EScore         float64 `json:"e_score"`
	SScore         float64 `json:"s_score"`
	GScore         float64 `json:"g_score"`
	CarbonEmissions float64 `json:"carbon_emissions"`
}

// Materialized View structures for caching (Response Models)
type SectorSummary struct {
	Sector        string  `json:"sector"`
	AvgEScore     float64 `json:"avg_e_score"`
	AvgSScore     float64 `json:"avg_s_score"`
	AvgGScore     float64 `json:"avg_g_score"`
	AvgTotalScore float64 `json:"avg_total_score"`
}

type TopCompany struct {
	Ticker       string  `json:"ticker"`
	SecurityName string  `json:"security_name"`
	EScore       float64 `json:"e_score"`
	SScore       float64 `json:"s_score"`
	GScore       float64 `json:"g_score"`
	TotalScore   float64 `json:"total_score"`
}
