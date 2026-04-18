import { create } from 'zustand';

/**
 * Global State Management for Sentinel AI Enterprise XDR.
 * Manages real-time telemetry, incidents, and threat intelligence state.
 */
const useXDRStore = create((set) => ({
  // Global Health Metrics
  stats: {
    processed_count: 0,
    incident_count: 0,
    threat_level: 'STABLE',
    active_chains: 0,
    velocity: 0
  },
  
  // Real-time Event Stream (Last 100 events)
  events: [],
  
  // Correlated Incidents
  incidents: [],
  
  // Intelligence Actions
  setStats: (newStats) => set((state) => ({ 
    stats: { ...state.stats, ...newStats } 
  })),
  
  addEvent: (event) => set((state) => ({ 
    events: [event, ...state.events].slice(0, 100) 
  })),
  
  setIncidents: (incidents) => set({ incidents }),
  
  updateIncident: (incidentId, updates) => set((state) => ({
    incidents: state.incidents.map((inc) => 
      inc.incident_id === incidentId ? { ...inc, ...updates } : inc
    )
  }))
}));

export default useXDRStore;
