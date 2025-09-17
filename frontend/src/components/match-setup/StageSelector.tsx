/**
 * Stage Selector Component
 * Dropdown for selecting league and stage configurations
 */

import React from 'react';

interface StageConfiguration {
  league: string;
  stage_name: string;
  targets: Array<{
    target_number: number;
    shape: string;
    type: string;
    category: string;
    distance: number;
    offset: number;
    height: number;
  }>;
}

interface StageSelectorProps {
  stageConfigurations: Record<string, Record<string, StageConfiguration>>;
  selectedLeague: string;
  selectedStage: string;
  onStageChange: (league: string, stage: string) => void;
  isLoading: boolean;
}

export const StageSelector: React.FC<StageSelectorProps> = ({
  stageConfigurations,
  selectedLeague,
  selectedStage,
  onStageChange,
  isLoading
}) => {
  // Get available leagues
  const leagues = Object.keys(stageConfigurations);
  


  const handleSelectionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (!value) return;
    
    const [league, stage] = value.split('::');
    onStageChange(league, stage);
  };

  const getCurrentValue = () => {
    if (selectedLeague && selectedStage) {
      return `${selectedLeague}::${selectedStage}`;
    }
    return '';
  };

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
        <span className="text-gray-600">Loading stages...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="stage-select" className="block text-sm font-medium text-gray-700 mb-2">
          Select Stage Configuration
        </label>
        <select
          id="stage-select"
          value={getCurrentValue()}
          onChange={handleSelectionChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select a stage...</option>
          {leagues.map(league => (
            <optgroup key={league} label={league}>
              {Object.keys(stageConfigurations[league] || {}).map(stage => (
                <option key={`${league}::${stage}`} value={`${league}::${stage}`}>
                  {stage}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      {/* Stage Info Display */}
      {selectedLeague && selectedStage && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">
                  {stageConfigurations[selectedLeague]?.[selectedStage]?.targets?.length || 0}
                </span>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-medium text-blue-900">
                {selectedLeague} - {selectedStage}
              </h3>
              <p className="text-blue-700 text-sm">
                {stageConfigurations[selectedLeague]?.[selectedStage]?.targets?.length || 0} targets configured
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};