
import { useLocalStorage } from "@mantine/hooks";
import axios from "axios";
import { createContext, useContext } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../App";

export interface UserProps { name: string, email: string, username: string }

export interface DefaultProps { user: UserProps, host: string }

export interface AuthContextProps {
  token: string,
  host: string,
  handleLogin: (username: string, password: string) => Promise<void>,
  handleLogout: () => void,
}

const AuthContext = createContext<AuthContextProps>({} as AuthContextProps);

export const useAuth = () => {
  return useContext(AuthContext);
};

export const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const { token } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export const AuthProvider = ({ children }: { children: JSX.Element }) => {
  const [token, setToken] = useLocalStorage<string>({ key: 'token', defaultValue: '' });
  // TODO make host a user selectable option
  const [host, setHost] = useLocalStorage<string>({ key: 'host', defaultValue: 'https://demo.inventree.org/api/' });

  function login(username: string, password: string) {
    return axios.get(`${host}user/token/`, { auth: { username, password } })
      .then((response) => response.data.token)
      .catch((error) => { console.log(error); });
  }

  // TODO add types
  const handleLogin = async (props: any) => {
    // Get token from server
    const form = props.form;
    const navigate = props.navigate;
    const token = await login(form.email, form.password);

    // Set token in context
    setToken(token);
    api.defaults.baseURL = host;
    api.defaults.headers.common['Authorization'] = `Token ${token}`;

    // Navigate to home page
    navigate('/');
  }

  const handleLogout = () => {
    console.log("Logout");
    setToken('');
  };

  const value = {
    token,
    host,
    handleLogin,
    handleLogout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
