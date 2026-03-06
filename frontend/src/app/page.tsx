"use client"
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getSectors, getEsgSummary, getTopCompanies } from "../api";
import { TopNav } from "../components/TopNav";
import { KPICards } from "../components/KPICards";
import { ESGChart } from "../components/ESGChart";
import { TopCompaniesTable } from "../components/TopCompaniesTable";

export default function Home() {
  const [selectedSector, setSelectedSector] = useState<string | undefined>(undefined);

  const { data: sectors = [], isLoading: isLoadingSectors } = useQuery({
    queryKey: ['sectors'],
    queryFn: getSectors,
  });

  const { data: summary = [], isLoading: isLoadingSummary, isError: isErrorSummary } = useQuery({
    queryKey: ['summary', selectedSector],
    queryFn: () => getEsgSummary(selectedSector),
  });

  const { data: topCompanies = [], isLoading: isLoadingCompanies, isError: isErrorCompanies } = useQuery({
    queryKey: ['top-companies', selectedSector],
    queryFn: () => getTopCompanies(selectedSector, 10),
  });

  const isLoading = isLoadingSectors || isLoadingSummary || isLoadingCompanies;
  const isError = isErrorSummary || isErrorCompanies;

  return (
    <div className="relative flex h-auto min-h-screen w-full flex-col group/design-root overflow-x-hidden">
      <div className="layout-container flex h-full grow flex-col">
        <div className="px-4 md:px-8 lg:px-12 flex flex-1 justify-center py-5">
          <div className="layout-content-container flex flex-col w-full max-w-[1200px] flex-1">
            <TopNav
              sectors={sectors}
              selectedSector={selectedSector}
              onSectorChange={setSelectedSector}
            />

            {isLoading ? (
              <div className="flex h-[50vh] items-center justify-center">
                <div className="w-12 h-12 border-4 border-slate-200 border-t-primary rounded-full animate-spin"></div>
              </div>
            ) : isError ? (
              <div className="flex h-[50vh] items-center justify-center">
                <p className="text-red-500 text-lg font-medium">Failed to load data. Please ensure API is running.</p>
              </div>
            ) : (
              <>
                <KPICards summary={summary} />
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                  <ESGChart data={summary} />
                  {/* Since the mockup has two charts (Bar Chart and Risk Score Trend), we map ESGChart to the Bar Chart. 
                      We can add a placeholder for the trend chart or leave it empty/replicate it if needed. 
                      For now, we just place the ESGChart spanning the required columns. */}
                </div>
                <TopCompaniesTable companies={topCompanies} />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
