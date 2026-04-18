import { useAuth0 } from "@auth0/auth0-react";

const LoginButton = () => {
  const { loginWithRedirect } = useAuth0();
  return (
    <button
      onClick={() => loginWithRedirect()}
      className="w-full bg-burgundy-600 hover:bg-burgundy-700 active:bg-burgundy-800 text-white font-semibold py-2.5 px-4 rounded-xl transition-colors duration-150 shadow-sm"
    >
      Sign In
    </button>
  );
};

export default LoginButton;