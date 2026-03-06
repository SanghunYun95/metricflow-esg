"use client"

interface TopNavProps {
    sectors: string[];
    selectedSector: string | undefined;
    onSectorChange: (sector: string | undefined) => void;
}

export function TopNav({ sectors, selectedSector, onSectorChange }: TopNavProps) {
    return (
        <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between whitespace-nowrap border-b border-solid border-border-dark pb-4 mb-6 gap-4">
            <div className="flex items-center gap-3 text-slate-900 dark:text-white">
                <span className="material-symbols-outlined text-primary">analytics</span>
                <h2 className="text-lg font-bold leading-tight tracking-tight">MetricFlow ESG</h2>
            </div>

            <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-text-muted hidden sm:inline-block">Filter by:</span>
                <div className="flex gap-2">
                    <div className="flex items-center justify-center rounded-md h-9 px-4 bg-surface-dark border border-border-dark text-slate-100 text-sm font-medium">
                        <span className="truncate">GICS Sector</span>
                    </div>
                    <div className="relative">
                        <select
                            value={selectedSector || ""}
                            onChange={(e) => onSectorChange(e.target.value || undefined)}
                            className="appearance-none flex items-center justify-between gap-2 rounded-md h-9 pl-4 pr-10 bg-primary text-white text-sm font-medium shadow-sm transition-colors hover:bg-primary/90 focus:outline-none cursor-pointer w-48 truncate"
                        >
                            <option value="">All Sectors</option>
                            {sectors.map((sector) => (
                                <option key={sector} value={sector} className="text-slate-900 bg-white dark:bg-surface-dark dark:text-white">
                                    {sector}
                                </option>
                            ))}
                        </select>
                        <span className="material-symbols-outlined text-[18px] text-white absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">arrow_drop_down</span>
                    </div>
                </div>
            </div>
        </header>
    );
}
