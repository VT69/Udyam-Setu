import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    axios.get(`${API_URL}/health`)
      .then(response => setHealth(response.data))
      .catch(error => console.error("Error fetching health:", error));
  }, []);

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Udyam Setu — Business Identity Resolution System</h1>
      <p>System Status: {health ? health.status : 'Loading...'}</p>
      {health && <pre>{JSON.stringify(health, null, 2)}</pre>}
    </div>
  );
}

export default App;
