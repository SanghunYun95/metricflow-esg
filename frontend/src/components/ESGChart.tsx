"use client"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { SectorSummary } from "../types/api";

export function ESGChart({ data }: { data: SectorSummary[] }) {
    if (!data || data.length === 0) return null;

    return (
        <div className="flex flex-col gap-4 rounded-lg bg-surface-dark border border-border-dark p-5 shadow-sm col-span-1 lg:col-span-2">
            <div className="flex justify-between items-start">
                <div>
                    <h3 className="text-base font-semibold">Sector E, S, G Averages</h3>
                    <p className="text-text-muted text-xs mt-1">Comparison of risk metric categories</p>
                </div>
            </div>
            <div className="mt-4 flex-1 min-h-[300px] w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={data}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5, }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#2d3f54" vertical={false} />
                        <XAxis dataKey="sector" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                        <Tooltip cursor={{ fill: '#2d3f54', opacity: 0.4 }} contentStyle={{ backgroundColor: '#1a2634', borderColor: '#2d3f54', color: '#f8fafc' }} />
                        <Legend wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
                        <Bar dataKey="avg_e_score" name="E Score" fill="#4ade80" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="avg_s_score" name="S Score" fill="#60a5fa" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="avg_g_score" name="G Score" fill="#c084fc" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
