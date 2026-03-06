"use client"
import { TopCompany } from "../types/api";

export function TopCompaniesTable({ companies }: { companies: TopCompany[] }) {
    if (!companies || companies.length === 0) return null;

    return (
        <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between px-1">
                <h2 className="text-lg font-bold leading-tight">Top Performing Companies</h2>
            </div>
            <div className="rounded-lg border border-border-dark bg-surface-dark overflow-x-auto shadow-sm">
                <table className="w-full text-left text-sm whitespace-nowrap">
                    <thead>
                        <tr className="bg-border-dark/30 text-text-muted border-b border-border-dark">
                            <th className="px-4 py-3 font-medium w-16">Rank</th>
                            <th className="px-4 py-3 font-medium">Company Name</th>
                            <th className="px-4 py-3 font-medium">Symbol</th>
                            <th className="px-4 py-3 font-medium text-right">E Score</th>
                            <th className="px-4 py-3 font-medium text-right">S Score</th>
                            <th className="px-4 py-3 font-medium text-right">G Score</th>
                            <th className="px-4 py-3 font-medium text-right">Total Risk</th>
                            <th className="px-4 py-3 font-medium text-center w-24">Status</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border-dark/50">
                        {companies.map((company, index) => {
                            // Example logic: < 20 Low, 20-30 Medium, > 30 High
                            const isLowRisk = company.total_score < 20;
                            const isMediumRisk = company.total_score >= 20 && company.total_score < 30;

                            const statusColor = isLowRisk ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                isMediumRisk ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                                    'bg-red-500/10 text-red-400 border-red-500/20';
                            const statusText = isLowRisk ? 'Low' : isMediumRisk ? 'Medium' : 'High';

                            return (
                                <tr key={company.ticker} className="hover:bg-border-dark/20 transition-colors">
                                    <td className="px-4 py-3 text-text-muted">{index + 1}</td>
                                    <td className="px-4 py-3 font-medium">{company.security_name}</td>
                                    <td className="px-4 py-3 text-text-muted">
                                        <span className="bg-border-dark/50 px-1.5 py-0.5 rounded text-xs">{company.ticker}</span>
                                    </td>
                                    <td className="px-4 py-3 text-right">{company.e_score.toFixed(1)}</td>
                                    <td className="px-4 py-3 text-right">{company.s_score.toFixed(1)}</td>
                                    <td className="px-4 py-3 text-right">{company.g_score.toFixed(1)}</td>
                                    <td className="px-4 py-3 text-right font-semibold">{company.total_score.toFixed(1)}</td>
                                    <td className="px-4 py-3 text-center">
                                        <span className={`inline-flex items-center justify-center px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider border w-full ${statusColor}`}>
                                            {statusText}
                                        </span>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
