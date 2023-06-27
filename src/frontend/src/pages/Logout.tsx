import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Logout() {
  const { handleLogout } = useAuth();
  const navigate = useNavigate();

  handleLogout();
  navigate('/');

  return <></>;
}
