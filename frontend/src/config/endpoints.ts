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
  private _isDevelopment?: boolean;
  private _baseHost?: string;
  private readonly apiPort: number = 8001;

  private get isDevelopment(): boolean {
    if (this._isDevelopment === undefined) {
      // Safely detect environment - fallback to production if window is not available
      try {
        this._isDevelopment = typeof window !== 'undefined' && 
          (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
      } catch {
        this._isDevelopment = false; // Default to production if window access fails
      }
    }
    return this._isDevelopment;
  }

  private get baseHost(): string {
    if (this._baseHost === undefined) {
      // Use pitts hostname for production, localhost for development
      this._baseHost = this.isDevelopment ? 'localhost' : 'pitts';
    }
    return this._baseHost;
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