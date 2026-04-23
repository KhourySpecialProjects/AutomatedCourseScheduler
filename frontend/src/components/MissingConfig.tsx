export default function MissingConfig({ missing }: { missing: string[] }) {
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
              <li key={k} className="font-mono">
                {k}
              </li>
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
