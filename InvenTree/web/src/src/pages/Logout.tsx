import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contex/AuthContext';

export function Logout() {
  const { handleLogout } = useAuth();
  const navigate = useNavigate();

  handleLogout();
  navigate('/');

  return <></>;
}
