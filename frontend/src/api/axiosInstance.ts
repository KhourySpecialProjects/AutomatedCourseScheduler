import axios from 'axios';
import type { AxiosRequestConfig } from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

// Back-compat: some parts of the app import `instance`.
export const instance = api;

export const axiosInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  return api(config).then(({ data }) => data);
};

export default api;
