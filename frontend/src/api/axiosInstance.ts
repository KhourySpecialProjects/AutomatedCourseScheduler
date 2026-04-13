import axios from 'axios';
import type { AxiosRequestConfig } from 'axios';

export const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

export const axiosInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  return instance(config).then(({ data }) => data);
};
