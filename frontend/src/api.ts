import axios from 'axios';
import { SectorSummary, TopCompany } from './types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
});

export const getSectors = async (): Promise<string[]> => {
    const { data } = await apiClient.get<string[]>('/sectors');
    return data;
};

export const getEsgSummary = async (sector?: string): Promise<SectorSummary[]> => {
    const params = sector ? { sector } : {};
    const { data } = await apiClient.get<SectorSummary[]>('/esg/summary', { params });
    return data;
};

export const getTopCompanies = async (sector?: string, limit: number = 10): Promise<TopCompany[]> => {
    const params = sector ? { sector, limit } : { limit };
    const { data } = await apiClient.get<TopCompany[]>('/esg/top-companies', { params });
    return data;
};
