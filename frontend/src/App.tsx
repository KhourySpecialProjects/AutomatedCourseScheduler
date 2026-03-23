import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Home from './pages/Home';
import Schedules from './pages/Schedules';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <span className="text-xl font-semibold text-gray-900">
                Course Scheduler
              </span>
              <div className="flex gap-6">
                <NavLink
                  to="/"
                  end
                  className={({ isActive }) =>
                    isActive
                      ? 'text-indigo-600 font-medium'
                      : 'text-gray-600 hover:text-gray-900'
                  }
                >
                  Home
                </NavLink>
                <NavLink
                  to="/schedules"
                  className={({ isActive }) =>
                    isActive
                      ? 'text-indigo-600 font-medium'
                      : 'text-gray-600 hover:text-gray-900'
                  }
                >
                  Schedules
                </NavLink>
                <NavLink
                  to="/sections"
                  className={({ isActive }) =>
                    isActive
                      ? 'text-indigo-600 font-medium'
                      : 'text-gray-600 hover:text-gray-900'
                  }
                >
                  Sections
                </NavLink>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/schedules" element={<Schedules />} />
            <Route path="/schedules/:scheduleId" element={<Schedules />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
