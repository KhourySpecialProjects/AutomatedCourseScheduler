import { useRef, useState } from 'react';
import { axiosInstance } from '../api/axiosInstance';
import type { UploadResponse } from '../api/generated';

type UploadKind = 'courses' | 'faculty-preferences' | 'time-preferences';

function prettyKind(kind: UploadKind): string {
  switch (kind) {
    case 'courses':
      return 'Courses offered';
    case 'faculty-preferences':
      return 'Course preferences';
    case 'time-preferences':
      return 'Time preferences';
  }
}

export default function Upload() {
  const [busy, setBusy] = useState<UploadKind | null>(null);
  const [result, setResult] = useState<{ kind: UploadKind; res: UploadResponse } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const coursesRef = useRef<HTMLInputElement>(null);
  const prefRef = useRef<HTMLInputElement>(null);
  const timeRef = useRef<HTMLInputElement>(null);

  async function doUpload(kind: UploadKind, file: File) {
    setError(null);
    setResult(null);
    setBusy(kind);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const url =
        kind === 'courses'
          ? '/upload/courses'
          : kind === 'faculty-preferences'
            ? '/upload/faculty-preferences'
            : '/upload/time-preferences';

      const res = await axiosInstance<UploadResponse>({
        url,
        method: 'POST',
        headers: { 'Content-Type': 'multipart/form-data' },
        data: formData,
      });
      setResult({ kind, res });
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail ??
        (e as { message?: unknown })?.message;
      setError(typeof detail === 'string' ? detail : 'Upload failed. Please check your CSV and try again.');
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Upload CSV</h1>
        <p className="mt-1 text-sm text-gray-500">Import courses, faculty, and preferences from CSV files.</p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {result && (
        <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-800">
          <div className="font-medium">{prettyKind(result.kind)} uploaded.</div>
          <div className="mt-1 text-xs text-emerald-700">
            {typeof result.res.message === 'string' ? result.res.message : 'Upload complete.'}
          </div>
          {result.res.errors?.length ? (
            <ul className="mt-2 list-disc list-inside text-xs text-emerald-800 space-y-0.5">
              {result.res.errors.slice(0, 8).map((e, i) => (
                <li key={i}>{e}</li>
              ))}
              {result.res.errors.length > 8 ? <li>…and {result.res.errors.length - 8} more</li> : null}
            </ul>
          ) : null}
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
        {/* Courses offered */}
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="text-sm font-semibold text-gray-900">Courses offered</div>
            <div className="text-xs text-gray-500">Upload the course catalog / offerings CSV.</div>
          </div>
          <div className="shrink-0 flex items-center gap-2">
            <input
              ref={coursesRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                void doUpload('courses', file);
                e.currentTarget.value = '';
              }}
            />
            <button
              type="button"
              disabled={busy !== null}
              onClick={() => coursesRef.current?.click()}
              className="px-3 py-2 text-xs font-medium bg-burgundy-600 text-white rounded-lg hover:bg-burgundy-700 disabled:opacity-50 transition-colors"
            >
              {busy === 'courses' ? 'Uploading…' : 'Upload CSV'}
            </button>
          </div>
        </div>

        <div className="h-px bg-gray-100" />

        {/* Course preferences */}
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="text-sm font-semibold text-gray-900">Course preferences</div>
            <div className="text-xs text-gray-500">Upload faculty course preference rankings CSV.</div>
          </div>
          <div className="shrink-0 flex items-center gap-2">
            <input
              ref={prefRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                void doUpload('faculty-preferences', file);
                e.currentTarget.value = '';
              }}
            />
            <button
              type="button"
              disabled={busy !== null}
              onClick={() => prefRef.current?.click()}
              className="px-3 py-2 text-xs font-medium bg-burgundy-600 text-white rounded-lg hover:bg-burgundy-700 disabled:opacity-50 transition-colors"
            >
              {busy === 'faculty-preferences' ? 'Uploading…' : 'Upload CSV'}
            </button>
          </div>
        </div>

        <div className="h-px bg-gray-100" />

        {/* Time preferences */}
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="text-sm font-semibold text-gray-900">Time preferences</div>
            <div className="text-xs text-gray-500">Upload faculty time preference rankings CSV.</div>
          </div>
          <div className="shrink-0 flex items-center gap-2">
            <input
              ref={timeRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                void doUpload('time-preferences', file);
                e.currentTarget.value = '';
              }}
            />
            <button
              type="button"
              disabled={busy !== null}
              onClick={() => timeRef.current?.click()}
              className="px-3 py-2 text-xs font-medium bg-burgundy-600 text-white rounded-lg hover:bg-burgundy-700 disabled:opacity-50 transition-colors"
            >
              {busy === 'time-preferences' ? 'Uploading…' : 'Upload CSV'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
