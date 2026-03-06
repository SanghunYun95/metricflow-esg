export interface SectorSummary {
    sector: string;
    avg_e_score: number;
    avg_s_score: number;
    avg_g_score: number;
    avg_total_score: number;
}

export interface TopCompany {
    ticker: string;
    security_name: string;
    e_score: number;
    s_score: number;
    g_score: number;
    total_score: number;
}
