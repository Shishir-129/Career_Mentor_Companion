import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Home() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // Replace this URL with your actual backend authentication endpoint
      const response = await fetch('https://api.yourdomain.com/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Fallback to a generic error if the server didn't provide a specific message
        throw new Error(data.message || 'Invalid email or password. Please try again.');
      }

      // 1. Save the token/session data securely
      // Your API might return data.token or data.accessToken depending on your backend schema
      localStorage.setItem('authToken', data.token); 
      
      // Optional: Save user profile info if your API sends it back
      if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
      }

      // 2. Redirect to the protected dashboard route
      navigate('/dashboard');

    } catch (err) {
      // Catch network errors or explicitly thrown server errors
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '400px', margin: '0 auto', textAlign: 'center' }}>
      <h1>Welcome Back</h1>
      
      {/* Visual feedback if something goes wrong */}
      {error && (
        <div style={{ color: 'red', backgroundColor: '#ffe6e6', padding: '10px', borderRadius: '4px', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSignIn} style={{ textAlign: 'left' }}>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="email" style={{ display: 'block', marginBottom: '0.5rem' }}>Email Address</label>
          <input 
            id="email"
            type="email" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            disabled={isLoading}
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
            required 
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label htmlFor="password" style={{ display: 'block', marginBottom: '0.5rem' }}>Password</label>
          <input 
            id="password"
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            disabled={isLoading}
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
            required 
          />
        </div>

        <button 
          type="submit" 
          disabled={isLoading}
          style={{ width: '100%', padding: '10px', cursor: isLoading ? 'not-allowed' : 'pointer' }}
        >
          {isLoading ? 'Signing In...' : 'Sign In'}
        </button>
      </form>
    </div>
  );
}