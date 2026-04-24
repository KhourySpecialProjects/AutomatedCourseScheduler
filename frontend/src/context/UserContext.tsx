import { createContext, useContext, useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { getAutomatedCourseSchedulerAPI, type UserResponse } from '../api/generated';

export type UserStatus = 'loading' | 'authorized' | 'blocked' | 'error';

interface UserContextValue {
  me: UserResponse | null;
  status: UserStatus;
  errorMessage: string | null;
  meError: string | null;
  meLoading: boolean;
}

const UserContext = createContext<UserContextValue>({
  me: null,
  status: 'loading',
  errorMessage: null,
  meError: null,
  meLoading: true,
});

export function UserProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth0();
  const [me, setMe] = useState<UserResponse | null>(null);
  const [status, setStatus] = useState<UserStatus>('loading');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    getAutomatedCourseSchedulerAPI()
      .getMeApiUsersMeGet()
      .then((user) => {
        setMe(user);
        setStatus('authorized');
      })
      .catch((err: unknown) => {
        const httpStatus = (err as { response?: { status?: number } })?.response?.status;
        if (httpStatus === 403) {
          setStatus('blocked');
          setErrorMessage(null);
        } else {
          setStatus('error');
          setErrorMessage('Could not load your user profile.');
        }
      });
  }, [isAuthenticated]);

  const value: UserContextValue = {
    me,
    status,
    errorMessage,
    meError: status === 'blocked'
      ? 'Your account is not authorized to use this application.'
      : errorMessage,
    meLoading: status === 'loading',
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  return useContext(UserContext);
}
