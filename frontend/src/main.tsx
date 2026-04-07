import React from 'react';
import ReactDOM from 'react-dom/client';
import { Auth0Provider } from '@auth0/auth0-react';
import App from './App.tsx';
import './index.css';

function MissingConfig({ missing }: { missing: string[] }) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h1 className="text-xl font-semibold text-gray-900">Frontend configuration missing</h1>
        <p className="mt-2 text-sm text-gray-600">
          Auth can’t start because required environment variables were not set at build/dev time.
        </p>

        <div className="mt-5">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Missing</div>
          <ul className="text-sm text-gray-800 space-y-1">
            {missing.map((k) => (
              <li key={k} className="font-mono">{k}</li>
            ))}
          </ul>
        </div>

        <div className="mt-6 text-sm text-gray-700">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Fix</div>
          <div className="font-mono text-xs bg-gray-50 border border-gray-200 rounded-lg p-3 whitespace-pre-wrap">
            {`cd frontend
cp .env.example .env
# then fill in the values and restart "npm run dev"`}
          </div>
        </div>
      </div>
    </div>
  );
}

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
        cacheLocation="memory"
      >
        <App />
      </Auth0Provider>
    )}
  </React.StrictMode>,
);
