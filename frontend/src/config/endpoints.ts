/**
 * Centralized endpoint configuration for LeadVille Bridge API
 * Handles environment-specific URLs and provides unified access points
 */

export interface EndpointConfig {
  getApiUrl(): string;
  getWebSocketUrl(channel: string): string;
  getBaseUrl(): string;
}

class EndpointConfigImpl implements EndpointConfig {
  private readonly isDevelopment: boolean;
  private readonly baseHost: string;
  private readonly apiPort: number;

  constructor() {
    // Detect environment - in development, we might be running on localhost
    this.isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    
    // Use pitts hostname for production, localhost for development
    this.baseHost = this.isDevelopment ? 'localhost' : 'pitts';
    this.apiPort = 8001;
  }

  getBaseUrl(): string {
    return `http://${this.baseHost}:${this.apiPort}`;
  }

  getApiUrl(): string {
    return `${this.getBaseUrl()}/api`;
  }

  getWebSocketUrl(channel: string): string {
    const wsProtocol = this.getBaseUrl().startsWith('https') ? 'wss' : 'ws';
    return `${wsProtocol}://${this.baseHost}:${this.apiPort}/ws/${channel}`;
  }
}

// Export singleton instance
export const endpointConfig = new EndpointConfigImpl();

// Export common endpoints for convenience
export const endpoints = {
  health: () => `${endpointConfig.getApiUrl()}/health`,
  logs: (limit?: number) => `${endpointConfig.getApiUrl()}/logs${limit ? `?limit=${limit}` : ''}`,
  devices: () => `${endpointConfig.getApiUrl()}/admin/devices`,
  stages: () => `${endpointConfig.getApiUrl()}/stages`,
  stageConfig: (league: string, stageName: string) => `${endpointConfig.getApiUrl()}/stages/${league}/${stageName}`,
} as const;