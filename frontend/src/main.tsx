import React from 'react';
import ReactDOM from 'react-dom/client';
import { Auth0Provider } from '@auth0/auth0-react';
import App from './App.tsx';
import MissingConfig from './components/MissingConfig.tsx';
import './index.css';

const required = [
  'VITE_AUTH0_DOMAIN',
  'VITE_AUTH0_CLIENT_ID',
  'VITE_AUTH0_AUDIENCE',
  'VITE_API_BASE_URL',
] as const;

const missing = required.filter((k) => !import.meta.env[k]);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {missing.length > 0 ? (
      <MissingConfig missing={missing} />
    ) : (
      <Auth0Provider
        domain={import.meta.env.VITE_AUTH0_DOMAIN}
        clientId={import.meta.env.VITE_AUTH0_CLIENT_ID}
        authorizationParams={{
          redirect_uri: window.location.origin,
          audience: import.meta.env.VITE_AUTH0_AUDIENCE,
        }}
        useRefreshTokens={true}
        // This may be insecure - jwt stored in browser memory
        cacheLocation="localstorage"
      >
        <App />
      </Auth0Provider>
    )}
  </React.StrictMode>,
);
