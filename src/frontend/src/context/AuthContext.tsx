import axios from 'axios';
import { createContext, useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { setApiDefaults } from '../App';
import { useLocalState } from './LocalState';
import { useSessionState } from './SessionState';

export interface AuthContextProps {
  token: string;
  host: string;
  handleLogin: (username: string, password: string) => Promise<void>;
  handleLogout: () => void;
}

const AuthContext = createContext<AuthContextProps>({} as AuthContextProps);

export const useAuth = () => {
  return useContext(AuthContext);
};

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const [token] = useSessionState((state) => [state.token]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export const AuthProvider = ({ children }: { children: JSX.Element }) => {
  const [token, setToken] = useSessionState((state) => [
    state.token,
    state.setToken
  ]);
  const [host] = useLocalState((state) => [state.host]);

  const handleLogin = async (username: string, password: string) => {
    // Get token from server
    const token = await axios
      .get(`${host}user/token/`, { auth: { username, password } })
      .then((response) => response.data.token)
      .catch((error) => {
        console.log(error);
      });

    // Set token in context
    setToken(token);
    setApiDefaults();
  };

  const handleLogout = () => {
    console.log('Logout');
    setToken('');
  };

  const value = {
    token,
    host,
    handleLogin,
    handleLogout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
