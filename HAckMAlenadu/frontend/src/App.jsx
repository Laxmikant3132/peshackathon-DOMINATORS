import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import Monitoring from './pages/Monitoring';
import useXDRStore from './store/useXDRStore';
import axios from 'axios';

const App = () => {
  const { setStats, addEvent, setIncidents } = useXDRStore();

  useEffect(() => {
    // 1. INITIAL DATA FETCH
    const fetchInitialData = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/incidents');
        setIncidents(res.data);
      } catch (err) {
        console.error("Initial fetch failed:", err);
      }
    };
    fetchInitialData();

    // 2. WEBSOCKET REAL-TIME CONNECTION
    const ws = new WebSocket('ws://localhost:8000/ws/telemetry');
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'STATS') {
        setStats(message.data);
      } else if (message.type === 'EVENT') {
        addEvent(message.data);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket Disconnected. Reconnecting in 5s...");
      setTimeout(() => window.location.reload(), 5000);
    };

    return () => ws.close();
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="monitoring" element={<Monitoring />} />
          {/* Stubs for other 11 pages will be added during phase 3 */}
          <Route path="*" element={<div className="p-10 text-slate-500 font-bold uppercase tracking-widest bg-white/5 rounded-xl border border-dashed border-white/10">Module in Development: Forensic Architecture v4.0 Patch Required</div>} />
        </Route>
      </Routes>
    </Router>
  );
};

export default App;
