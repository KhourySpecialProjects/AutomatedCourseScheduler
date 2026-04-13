import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import ScheduleList from './pages/ScheduleList';
import Schedules from './pages/Schedules';
import Faculty from './pages/Faculty';
import Courses from './pages/Courses';
import Upload from './pages/Upload';
import Sidebar from './components/Sidebar';
import LoginButton from './components/LoginButton';
import { useAuthInterceptor } from './hooks/useAuthInterceptor';

function App() {
  const { isAuthenticated, isLoading, error } = useAuth0();
  useAuthInterceptor();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-gray-500">
          <div className="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          <span className="text-sm font-medium">Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-sm border border-red-100 p-8 max-w-sm w-full text-center">
          <div className="text-3xl mb-2">⚠️</div>
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Something went wrong</h2>
          <p className="text-sm text-gray-500">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      {!isAuthenticated ? (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-slate-50 flex items-center justify-center px-4">
          <div className="w-full max-w-md">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-600 rounded-2xl mb-4 shadow-lg">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Course Scheduler</h1>
              <p className="mt-2 text-gray-500 text-sm">Automated scheduling for academic programs</p>
            </div>
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
              <p className="text-gray-600 text-sm text-center mb-6">Sign in to manage schedules, sections, and more.</p>
              <LoginButton />
            </div>
          </div>
        </div>
      ) : (
        <div className="flex h-screen overflow-hidden bg-gray-50">
          <Sidebar />
          <main className="flex-1 overflow-y-auto">
            <div className="p-8">
              <Routes>
                <Route path="/" element={<Navigate to="/schedules" replace />} />
                <Route path="/schedules" element={<ScheduleList />} />
                <Route path="/schedules/:scheduleId" element={<Schedules />} />
                <Route path="/faculty/schedules/:scheduleId" element={<Schedules readOnly />} />
                <Route path="/faculty" element={<Faculty />} />
                <Route path="/courses" element={<Courses />} />
                <Route path="/upload" element={<Upload />} />
              </Routes>
            </div>
          </main>
        </div>
      )}
    </BrowserRouter>
  );
}

export default App;
