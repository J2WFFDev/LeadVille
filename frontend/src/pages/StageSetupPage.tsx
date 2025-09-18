/**
 * Stage Setup Component - Visual stage layout and sensor assignment
 */

import React, { useState, useEffect } from 'react';

interface League {
  id: number;
  name: string;
  abbreviation: string;
  description: string;
}

interface Target {
  id: number;
  target_number: number;
  shape: string;
  type: string;
  category: string;
  distance_feet: number;
  offset_feet: number;
  height_feet: number;
  sensor?: {
    id: number;
    hw_addr: string;
    label: string;
    last_seen: string | null;
    battery: number | null;
    rssi: number | null;
  };
}

interface Stage {
  id: number;
  name: string;
  description: string;
  target_count: number;
  targets: Target[];
}

interface Sensor {
  id: number;
  hw_addr: string;
  label: string;
  last_seen: string | null;
  battery: number | null;
  rssi: number | null;
  assigned: boolean;
}

export const StageSetupPage: React.FC = () => {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<League | null>(null);
  const [stages, setStages] = useState<Stage[]>([]);
  const [selectedStage, setSelectedStage] = useState<Stage | null>(null);
  const [stageDetails, setStageDetails] = useState<any>(null);
  const [availableSensors, setAvailableSensors] = useState<Sensor[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load leagues on component mount
  useEffect(() => {
    loadLeagues();
    loadAvailableSensors();
  }, []);

  // Load stages when league is selected
  useEffect(() => {
    if (selectedLeague) {
      loadLeagueStages(selectedLeague.id);
    }
  }, [selectedLeague]);

  // Load stage details when stage is selected
  useEffect(() => {
    if (selectedStage) {
      loadStageDetails(selectedStage.id);
    }
  }, [selectedStage]);

  const loadLeagues = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/leagues');
      const data = await response.json();
      
      if (response.ok) {
        setLeagues(data.leagues);
      } else {
        setError(data.error || 'Failed to load leagues');
      }
    } catch (err) {
      setError('Network error loading leagues');
    } finally {
      setLoading(false);
    }
  };

  const loadLeagueStages = async (leagueId: number) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/admin/leagues/${leagueId}/stages`);
      const data = await response.json();
      
      if (response.ok) {
        setStages(data.stages);
      } else {
        setError(data.error || 'Failed to load stages');
      }
    } catch (err) {
      setError('Network error loading stages');
    } finally {
      setLoading(false);
    }
  };

  const loadStageDetails = async (stageId: number) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/admin/stages/${stageId}`);
      const data = await response.json();
      
      if (response.ok) {
        setStageDetails(data.stage);
      } else {
        setError(data.error || 'Failed to load stage details');
      }
    } catch (err) {
      setError('Network error loading stage details');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableSensors = async () => {
    try {
      const response = await fetch('/api/admin/devices');
      const data = await response.json();
      
      if (response.ok) {
        // Show all paired sensors
        const sensors = data.devices
          .filter((device: any) => device.type === 'sensor')
          .map((device: any) => ({
            id: device.id,
            hw_addr: device.address || device.hw_addr,
            label: device.label || `Sensor ${device.address || device.hw_addr}`,
            last_seen: device.last_seen,
            battery: device.battery,
            rssi: device.rssi,
            assigned: device.target_config_id !== null
          }));
        
        setAvailableSensors(sensors);
      }
    } catch (err) {
      console.error('Failed to load sensors:', err);
    }
  };

  const assignSensorToTarget = async (targetNumber: number, sensorId: number) => {
    if (!selectedStage) return;

    try {
      const response = await fetch(`/api/admin/stages/${selectedStage.id}/assign_sensor`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sensor_id: sensorId,
          target_number: targetNumber
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        // Reload stage details and available sensors
        await loadStageDetails(selectedStage.id);
        await loadAvailableSensors();
        alert(data.message);
      } else {
        alert(`Failed to assign sensor: ${data.error}`);
      }
    } catch (err) {
      alert('Network error assigning sensor');
    }
  };

  const unassignSensorFromTarget = async (targetNumber: number) => {
    if (!selectedStage) return;

    try {
      const response = await fetch(`/api/admin/stages/${selectedStage.id}/unassign_sensor`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_number: targetNumber
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        // Reload stage details and available sensors
        await loadStageDetails(selectedStage.id);
        await loadAvailableSensors();
        alert(data.message);
      } else {
        alert(`Failed to unassign sensor: ${data.error}`);
      }
    } catch (err) {
      alert('Network error unassigning sensor');
    }
  };

  const renderTargetVisual = (target: Target) => {
    const isStop = target.category === 'Stop';
    const isPenalty = target.category === 'Penalty';
    const isGong = target.type === 'Gong';
    
    return (
      <div
        key={target.id}
        style={{
          position: 'absolute',
          left: `${50 + (target.offset_feet * 2)}%`,
          bottom: `${10 + (target.distance_feet / 2)}px`,
          transform: 'translateX(-50%)',
          width: isGong ? '40px' : '30px',
          height: isGong ? '60px' : '30px',
          borderRadius: isGong ? '8px' : '50%',
          backgroundColor: isStop ? '#ef4444' : isPenalty ? '#f59e0b' : '#3b82f6',
          border: '2px solid #ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '12px',
          fontWeight: 'bold',
          cursor: 'pointer',
          boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
        }}
        title={`Target ${target.target_number}: ${target.shape} ${target.type} (${target.category})`}
      >
        {target.target_number}
      </div>
    );
  };

  const renderStageLayout = () => {
    if (!stageDetails) return null;

    return (
      <div style={{ 
        position: 'relative', 
        width: '100%', 
        height: '400px', 
        backgroundColor: '#f3f4f6',
        border: '2px solid #d1d5db',
        borderRadius: '8px',
        overflow: 'hidden'
      }}>
        {/* Shooting position */}
        <div style={{
          position: 'absolute',
          bottom: '10px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '20px',
          height: '20px',
          backgroundColor: '#10b981',
          borderRadius: '50%',
          border: '2px solid #ffffff'
        }} title="Shooting Position" />
        
        {/* Distance markers */}
        {[10, 20, 30, 40, 50, 60, 70].map(distance => (
          <div
            key={distance}
            style={{
              position: 'absolute',
              bottom: `${10 + distance}px`,
              left: '0',
              right: '0',
              height: '1px',
              backgroundColor: '#d1d5db',
              opacity: 0.5
            }}
          />
        ))}
        
        {/* Distance labels */}
        {[20, 40, 60].map(distance => (
          <div
            key={distance}
            style={{
              position: 'absolute',
              bottom: `${5 + distance}px`,
              left: '10px',
              fontSize: '10px',
              color: '#6b7280'
            }}
          >
            {distance}'
          </div>
        ))}

        {/* Targets */}
        {stageDetails.targets.map(renderTargetVisual)}
      </div>
    );
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 'bold', color: '#1f2937', margin: 0 }}>
          🎯 Stage Setup
        </h1>
        <p style={{ color: '#6b7280', marginTop: '8px' }}>
          Configure stages and assign sensors to targets
        </p>
      </div>

      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          padding: '12px',
          marginBottom: '20px',
          color: '#991b1b'
        }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '24px' }}>
        {/* Left Panel - League/Stage Selection */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          padding: '20px'
        }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
            Select Stage
          </h2>

          {/* League Selection */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
              League
            </label>
            <select
              value={selectedLeague?.id || ''}
              onChange={(e) => {
                const league = leagues.find(l => l.id === parseInt(e.target.value));
                setSelectedLeague(league || null);
                setSelectedStage(null);
                setStageDetails(null);
              }}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            >
              <option value="">Select League...</option>
              {leagues.map(league => (
                <option key={league.id} value={league.id}>
                  {league.name}
                </option>
              ))}
            </select>
          </div>

          {/* Stage Selection */}
          {selectedLeague && (
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
                Stage
              </label>
              <select
                value={selectedStage?.id || ''}
                onChange={(e) => {
                  const stage = stages.find(s => s.id === parseInt(e.target.value));
                  setSelectedStage(stage || null);
                }}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              >
                <option value="">Select Stage...</option>
                {stages.map(stage => (
                  <option key={stage.id} value={stage.id}>
                    {stage.name} ({stage.target_count} targets)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Available Sensors */}
          {availableSensors.length > 0 && (
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
                Available Sensors
              </h3>
              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                {availableSensors.filter(s => !s.assigned).map(sensor => (
                  <div
                    key={sensor.id}
                    style={{
                      padding: '8px',
                      marginBottom: '8px',
                      backgroundColor: '#f9fafb',
                      border: '1px solid #e5e7eb',
                      borderRadius: '6px',
                      fontSize: '12px'
                    }}
                  >
                    <div style={{ fontWeight: '500' }}>{sensor.label}</div>
                    <div style={{ color: '#6b7280' }}>{sensor.hw_addr}</div>
                    {sensor.battery && (
                      <div style={{ color: '#059669' }}>Battery: {sensor.battery}%</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Stage Visualization and Target Management */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          padding: '20px'
        }}>
          {stageDetails ? (
            <>
              <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
                {stageDetails.league.name} - {stageDetails.name}
              </h2>

              {/* Stage Layout Visualization */}
              <div style={{ marginBottom: '24px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '500', marginBottom: '12px' }}>
                  Stage Layout
                </h3>
                {renderStageLayout()}
              </div>

              {/* Target Assignment Table */}
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '500', marginBottom: '12px' }}>
                  Sensor Assignments
                </h3>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f9fafb' }}>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Target</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Type</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Category</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Distance</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Sensor</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stageDetails.targets.map((target: Target) => (
                        <tr key={target.id}>
                          <td style={{ padding: '12px', borderBottom: '1px solid #e5e7eb' }}>
                            <span style={{ fontWeight: '500' }}>Target {target.target_number}</span>
                            <br />
                            <span style={{ fontSize: '12px', color: '#6b7280' }}>{target.shape}</span>
                          </td>
                          <td style={{ padding: '12px', borderBottom: '1px solid #e5e7eb' }}>{target.type}</td>
                          <td style={{ padding: '12px', borderBottom: '1px solid #e5e7eb' }}>
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: '12px',
                              fontSize: '12px',
                              backgroundColor: target.category === 'Stop' ? '#fef2f2' : target.category === 'Penalty' ? '#fefce8' : '#eff6ff',
                              color: target.category === 'Stop' ? '#991b1b' : target.category === 'Penalty' ? '#92400e' : '#1e40af'
                            }}>
                              {target.category}
                            </span>
                          </td>
                          <td style={{ padding: '12px', borderBottom: '1px solid #e5e7eb' }}>
                            {target.distance_feet}' @ {target.offset_feet}'
                          </td>
                          <td style={{ padding: '12px', borderBottom: '1px solid #e5e7eb' }}>
                            {target.sensor ? (
                              <div>
                                <div style={{ fontWeight: '500' }}>{target.sensor.label}</div>
                                <div style={{ fontSize: '12px', color: '#6b7280' }}>{target.sensor.hw_addr}</div>
                                {target.sensor.battery && (
                                  <div style={{ fontSize: '12px', color: '#059669' }}>
                                    Battery: {target.sensor.battery}%
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>Unassigned</span>
                            )}
                          </td>
                          <td style={{ padding: '12px', borderBottom: '1px solid #e5e7eb' }}>
                            {target.sensor ? (
                              <button
                                onClick={() => unassignSensorFromTarget(target.target_number)}
                                style={{
                                  padding: '4px 8px',
                                  backgroundColor: '#ef4444',
                                  color: 'white',
                                  border: 'none',
                                  borderRadius: '4px',
                                  fontSize: '12px',
                                  cursor: 'pointer'
                                }}
                              >
                                Remove
                              </button>
                            ) : (
                              <select
                                onChange={(e) => {
                                  if (e.target.value) {
                                    assignSensorToTarget(target.target_number, parseInt(e.target.value));
                                    e.target.value = '';
                                  }
                                }}
                                style={{
                                  padding: '4px 8px',
                                  border: '1px solid #d1d5db',
                                  borderRadius: '4px',
                                  fontSize: '12px'
                                }}
                              >
                                <option value="">Assign Sensor...</option>
                                {availableSensors.filter(s => !s.assigned).map(sensor => (
                                  <option key={sensor.id} value={sensor.id}>
                                    {sensor.label}
                                  </option>
                                ))}
                              </select>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : selectedStage ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
              Loading stage details...
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
              Select a league and stage to configure sensor assignments
            </div>
          )}
        </div>
      </div>

      {loading && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            Loading...
          </div>
        </div>
      )}
    </div>
  );
};