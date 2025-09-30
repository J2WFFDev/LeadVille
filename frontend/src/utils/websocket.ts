/**
 * WebSocket client for LeadVille Bridge real-time communication
 * Connects to the Python WebSocket server for timer and sensor events
 */

import { endpointConfig } from '../config/endpoints';

export interface TimerEvent {
  type: 'timer_event';
  event_type: string;
  timestamp: string;
  device_id: string;
  data: {
    shot_state?: string;
    current_shot?: number;
    current_time?: number;
    event_detail?: string;
  };
}

export interface HealthStatus {
  type: 'health_status';
  timestamp: string;
  device_id: string;
  data: {
    connection_status: string;
    rssi_dbm?: number;
    uptime_seconds?: number;
    data_rate_events_per_sec?: number;
  };
}

export interface SessionUpdate {
  type: 'session_update';
  timestamp: string;
  data: {
    session_id?: string;
    state?: string;
    shots?: number;
    duration?: number;
  };
}

export type WebSocketMessage = TimerEvent | HealthStatus | SessionUpdate;

export interface WebSocketConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
}

export class LeadVilleWebSocketClient {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private isConnected = false;
  private reconnectTimeout: number | null = null;
  
  // Event handlers
  private onMessageHandlers: ((message: WebSocketMessage) => void)[] = [];
  private onConnectionHandlers: ((connected: boolean) => void)[] = [];
  private onErrorHandlers: ((error: Event) => void)[] = [];

  constructor(config: Partial<WebSocketConfig> = {}) {
    this.config = {
      url: endpointConfig.getWebSocketUrl('live'),
      reconnectInterval: 3000,
      maxReconnectAttempts: 10,
      ...config
    };
  }

  connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    try {
      this.ws = new WebSocket(this.config.url);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected to LeadVille Bridge');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.notifyConnectionHandlers(true);
        
        // Subscribe to all channels on connect
        this.subscribe(['timer_events', 'health_status', 'session_updates']);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.notifyMessageHandlers(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnected = false;
        this.notifyConnectionHandlers(false);
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.notifyErrorHandlers(error);
      };

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      this.attemptReconnect();
    }
  }

  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnected = false;
    this.reconnectAttempts = 0;
  }

  subscribe(channels: string[]): void {
    if (!this.isConnected || !this.ws) {
      console.warn('Cannot subscribe: WebSocket not connected');
      return;
    }

    const subscribeMessage = {
      type: 'subscribe',
      channels: channels
    };

    this.ws.send(JSON.stringify(subscribeMessage));
  }

  sendPing(): void {
    if (!this.isConnected || !this.ws) {
      return;
    }

    const pingMessage = {
      type: 'ping'
    };

    this.ws.send(JSON.stringify(pingMessage));
  }

  // Event handler management
  onMessage(handler: (message: WebSocketMessage) => void): () => void {
    this.onMessageHandlers.push(handler);
    return () => {
      const index = this.onMessageHandlers.indexOf(handler);
      if (index > -1) {
        this.onMessageHandlers.splice(index, 1);
      }
    };
  }

  onConnection(handler: (connected: boolean) => void): () => void {
    this.onConnectionHandlers.push(handler);
    return () => {
      const index = this.onConnectionHandlers.indexOf(handler);
      if (index > -1) {
        this.onConnectionHandlers.splice(index, 1);
      }
    };
  }

  onError(handler: (error: Event) => void): () => void {
    this.onErrorHandlers.push(handler);
    return () => {
      const index = this.onErrorHandlers.indexOf(handler);
      if (index > -1) {
        this.onErrorHandlers.splice(index, 1);
      }
    };
  }

  // Private methods
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})...`);

    this.reconnectTimeout = window.setTimeout(() => {
      this.connect();
    }, this.config.reconnectInterval);
  }

  private notifyMessageHandlers(message: WebSocketMessage): void {
    this.onMessageHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
  }

  private notifyConnectionHandlers(connected: boolean): void {
    this.onConnectionHandlers.forEach(handler => {
      try {
        handler(connected);
      } catch (error) {
        console.error('Error in connection handler:', error);
      }
    });
  }

  private notifyErrorHandlers(error: Event): void {
    this.onErrorHandlers.forEach(handler => {
      try {
        handler(error);
      } catch (error) {
        console.error('Error in error handler:', error);
      }
    });
  }

  // Getters
  get connected(): boolean {
    return this.isConnected;
  }

  get connectionState(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'closed';
      default: return 'unknown';
    }
  }
}

// Export a singleton instance
export const wsClient = new LeadVilleWebSocketClient();