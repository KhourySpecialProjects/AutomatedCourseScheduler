import { useAuth0 } from '@auth0/auth0-react';

const AccessDenied = () => {
  const { user, logout } = useAuth0();

  const handleLogout = () => {
    logout({ logoutParams: { returnTo: window.location.origin } });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-burgundy-50 via-white to-slate-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <img
            src="/acs-logo.png"
            alt="ACS Automated Course Scheduler"
            className="h-16 w-auto max-w-full mx-auto mb-4 object-contain drop-shadow-sm"
          />
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Access denied</h1>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <p className="text-gray-700 text-sm text-center mb-2">
            {user?.email ? (
              <>
                <span className="font-medium text-gray-900">{user.email}</span> is not authorized to use this application.
              </>
            ) : (
              'Your account is not authorized to use this application.'
            )}
          </p>
          <p className="text-gray-500 text-sm text-center mb-6">
            Contact an administrator if you believe this is a mistake.
          </p>
          <button
            onClick={handleLogout}
            className="w-full bg-burgundy-600 hover:bg-burgundy-700 active:bg-burgundy-800 text-white font-semibold py-2.5 px-4 rounded-xl transition-colors duration-150 shadow-sm"
          >
            Log out
          </button>
        </div>
      </div>
    </div>
  );
};

export default AccessDenied;
