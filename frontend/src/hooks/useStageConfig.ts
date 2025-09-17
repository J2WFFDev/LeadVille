/**
 * Custom hook for managing stage configurations
 */

import { useState, useEffect } from 'react';

interface Target {
  target_number: number;
  shape: string;
  type: string;
  category: string;
  distance: number;
  offset: number;
  height: number;
}

interface StageConfiguration {
  league: string;
  stage_name: string;
  targets: Target[];
}

type StageConfigurations = Record<string, Record<string, StageConfiguration>>;

export const useStageConfig = () => {
  const [stageConfigurations, setStageConfigurations] = useState<StageConfigurations>({});
  const [currentStageConfig, setCurrentStageConfig] = useState<StageConfiguration | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load all stage configurations from API
  const loadStageConfigurations = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://192.168.1.124:8001/api/stages');
      if (!response.ok) {
        throw new Error(`Failed to load stages: ${response.statusText}`);
      }
      
      const data = await response.json();
      setStageConfigurations(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error loading stage configurations:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Load specific stage configuration
  const loadStageConfig = async (league: string, stageName: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://192.168.1.124:8001/api/stages/${league}/${stageName}`);
      if (!response.ok) {
        throw new Error(`Failed to load stage: ${response.statusText}`);
      }
      
      const data = await response.json();
      setCurrentStageConfig(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error loading stage configuration:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Convert stage data from API format
  const convertStageFromAPI = (stageData: any): StageConfiguration => {
    return {
      league: stageData.league,
      stage_name: stageData.stage_name,
      targets: stageData.targets || []
    };
  };

  // Initialize stage configurations on mount
  useEffect(() => {
    loadStageConfigurations();
  }, []);

  return {
    stageConfigurations,
    currentStageConfig,
    isLoading,
    error,
    loadStageConfigurations,
    loadStageConfig,
    convertStageFromAPI
  };
};