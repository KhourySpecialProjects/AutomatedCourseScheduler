import { createContext, useContext, useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { getAutomatedCourseSchedulerAPI, type UserResponse } from '../api/generated';

interface UserContextValue {
  me: UserResponse | null;
  meError: string | null;
  meLoading: boolean;
}

const UserContext = createContext<UserContextValue>({ me: null, meError: null, meLoading: true });

export function UserProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth0();
  const [me, setMe] = useState<UserResponse | null>(null);
  const [meError, setMeError] = useState<string | null>(null);
  const [meLoading, setMeLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) return;
    getAutomatedCourseSchedulerAPI()
      .getMeApiUsersMeGet()
      .then(setMe)
      .catch((err: unknown) => {
        const status = (err as { response?: { status?: number } })?.response?.status;
        setMeError(
          status === 403
            ? 'Your Auth0 account is not linked to a DB user yet. Ask an admin to invite you or run bootstrap_admin.py.'
            : 'Could not load your user profile.',
        );
      })
      .finally(() => setMeLoading(false));
  }, [isAuthenticated]);

  return <UserContext.Provider value={{ me, meError, meLoading }}>{children}</UserContext.Provider>;
}

export function useUser() {
  return useContext(UserContext);
}
