"use client"
import { SectorSummary } from "../types/api";

export function KPICards({ summary }: { summary: SectorSummary[] }) {
    if (!summary || summary.length === 0) return null;
    const data = summary[0];

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <Card title="Avg Environmental Risk" value={data.avg_e_score.toFixed(1)} icon="eco" iconColor="text-green-400" />
            <Card title="Avg Social Risk" value={data.avg_s_score.toFixed(1)} icon="groups" iconColor="text-blue-400" />
            <Card title="Avg Governance Risk" value={data.avg_g_score.toFixed(1)} icon="gavel" iconColor="text-purple-400" />
            <TotalRiskCard value={data.avg_total_score.toFixed(1)} />
        </div>
    );
}

function Card({ title, value, icon, iconColor }: { title: string, value: string, icon: string, iconColor: string }) {
    return (
        <div className="flex flex-col gap-2 rounded-lg p-5 bg-surface-dark border border-border-dark shadow-sm">
            <div className="flex justify-between items-start">
                <p className="text-text-muted text-sm font-medium">{title}</p>
                <span className={`material-symbols-outlined ${iconColor} text-[20px]`}>{icon}</span>
            </div>
            <div className="flex items-baseline gap-2 mt-1">
                <p className="text-2xl font-bold">{value}</p>
            </div>
            <div className="h-8 mt-2 w-full flex items-end gap-1">
                <div className="w-full h-[30%] bg-border-dark rounded-t-sm"></div>
                <div className="w-full h-[40%] bg-border-dark rounded-t-sm"></div>
                <div className="w-full h-[25%] bg-border-dark rounded-t-sm"></div>
                <div className="w-full h-[50%] bg-border-dark rounded-t-sm"></div>
                <div className="w-full h-[35%] bg-border-dark rounded-t-sm"></div>
                <div className="w-full h-[60%] bg-border-dark rounded-t-sm"></div>
                <div className="w-full h-[20%] bg-border-dark rounded-t-sm"></div>
            </div>
        </div>
    );
}

function TotalRiskCard({ value }: { value: string }) {
    return (
        <div className="flex flex-col gap-2 rounded-lg p-5 bg-primary/10 border border-primary/30 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10">
                <span className="material-symbols-outlined text-[64px] text-primary">monitoring</span>
            </div>
            <div className="flex justify-between items-start relative z-10">
                <p className="text-primary text-sm font-semibold">Total ESG Risk Score</p>
            </div>
            <div className="flex items-baseline gap-2 mt-1 relative z-10">
                <p className="text-3xl font-bold text-white">{value}</p>
            </div>
            <div className="mt-auto pt-2 relative z-10">
                <div className="w-full bg-surface-dark rounded-full h-1.5 border border-border-dark">
                    <div className="bg-primary h-1.5 rounded-full" style={{ width: '62%' }}></div>
                </div>
                <p className="text-xs text-text-muted mt-1 text-right">Target: <span className="text-white">55.0</span></p>
            </div>
        </div>
    );
}
