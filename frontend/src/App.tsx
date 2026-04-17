import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import ScheduleList from './pages/ScheduleList';
import Schedules from './pages/Schedules';
import Faculty from './pages/Faculty';
import Courses from './pages/Courses';
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
          <div className="w-8 h-8 border-4 border-burgundy-200 border-t-burgundy-600 rounded-full animate-spin" />
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
        <div className="min-h-screen bg-gradient-to-br from-burgundy-50 via-white to-slate-50 flex items-center justify-center px-4">
          <div className="w-full max-w-md">
            <div className="text-center mb-8">
              <img
                src="/acs-logo.png"
                alt="ACS Automated Course Scheduler"
                className="h-16 w-auto max-w-full mx-auto mb-4 object-contain drop-shadow-sm"
              />
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
              </Routes>
            </div>
          </main>
        </div>
      )}
    </BrowserRouter>
  );
}

export default App;
