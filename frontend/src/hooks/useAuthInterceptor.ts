import { useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { instance } from '../api/axiosInstance';

export function useAuthInterceptor() {
  const { getAccessTokenSilently } = useAuth0();

  useEffect(() => {
    const interceptorId = instance.interceptors.request.use(async (config) => {
      try {
        const token = await getAccessTokenSilently();
        config.headers.Authorization = `Bearer ${token}`;
      } catch {
        // not authenticated, send request without token
      }
      return config;
    });

    return () => {
      instance.interceptors.request.eject(interceptorId);
    };
  }, [getAccessTokenSilently]);
}
