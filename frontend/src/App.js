import { useState, useEffect } from 'react';
import './App.css';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import { Toaster } from './components/ui/toaster';

function App() {
  const [apiKey, setApiKey] = useState(localStorage.getItem('unbound_key'));
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (apiKey) {
      const storedUser = localStorage.getItem('unbound_user');
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
    }
  }, [apiKey]);

  const handleLogin = (key, userData) => {
    localStorage.setItem('unbound_key', key);
    localStorage.setItem('unbound_user', JSON.stringify(userData));
    setApiKey(key);
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('unbound_key');
    localStorage.removeItem('unbound_user');
    setApiKey(null);
    setUser(null);
  };

  return (
    <div className="App min-h-screen bg-slate-950 text-white">
      {!apiKey || !user ? (
        <Login onLogin={handleLogin} />
      ) : (
        <Dashboard apiKey={apiKey} user={user} onLogout={handleLogout} />
      )}
      <Toaster />
    </div>
  );
}

export default App;
