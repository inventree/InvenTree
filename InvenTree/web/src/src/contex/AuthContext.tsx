
import { useLocalStorage } from "@mantine/hooks";
import axios from "axios";
import { createContext, useContext } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../App";
import { ReactNode } from "react";

export type UserProps = {
  name: string,
  email: string,
  username: string,
}

export type DefaultProps = {
  user: UserProps,
  host: string,
}

export type AuthContextProps = {
  token: string,
  host: string,
  handleLogin: (username: string, password: string) => Promise<void>,
}

const AuthContext = createContext<AuthContextProps>({} as AuthContextProps);

export const useAuth = () => {
  return useContext(AuthContext);
};

export const ProtectedRoute = (children: ReactNode) => {
  const { token } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export const AuthProvider = (children: ReactNode) => {
  const [token, setToken] = useLocalStorage<string>({key: 'token', defaultValue: ''});
  // TODO make host a user selectable option
  const [host, setHost] = useLocalStorage<string>({key: 'host', defaultValue: 'http://127.0.0.1:8000/api/'});

  function login(username: string, password: string) {
    return axios.get(`${host}user/token/`, {auth:{ username, password} })
      .then((response) => response.data.token)
      .catch((error) => {console.log(error);});
  }

  // TODO add types
  const handleLogin = async (props: any) => {
    // Get token from server
    const form = props.form;
    const navigate = props.navigate;
    const token = await login(form.email, form.password);

    // Set token in context
    setToken(token);
    api.defaults.baseURL=host;
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
    onLogin: handleLogin,
    onLogout: handleLogout,
    handleLogin,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
