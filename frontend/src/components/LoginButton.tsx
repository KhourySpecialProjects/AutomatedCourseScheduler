import { useAuth0 } from "@auth0/auth0-react";

const LoginButton = () => {
  const { loginWithRedirect } = useAuth0();
  return (
    <button
      onClick={() => loginWithRedirect()}
      className="w-full bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white font-semibold py-2.5 px-4 rounded-xl transition-colors duration-150 shadow-sm"
    >
      Sign In
    </button>
  );
};

export default LoginButton;