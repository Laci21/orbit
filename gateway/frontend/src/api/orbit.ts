/**
 * API client for Orbit Crisis Management Gateway
 */
import React from 'react';

const API_BASE_URL = 'http://localhost:8000/api';

export interface CrisisStatus {
  crisis_id: string | null;
  status: 'idle' | 'active' | 'complete' | 'error';
  started_at: string | null;
  final_response: any | null;
  last_update: string | null;
}

export interface TriggerCrisisRequest {
  tweet_content?: string;
}

export interface TriggerCrisisResponse {
  success: boolean;
  crisis_id: string;
  message: string;
}

/**
 * Get current crisis status
 */
export async function getCrisisStatus(): Promise<CrisisStatus> {
  const response = await fetch(`${API_BASE_URL}/crisis/status`);
  
  if (!response.ok) {
    throw new Error(`Failed to get crisis status: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Trigger a new crisis for demo purposes
 */
export async function triggerCrisis(request: TriggerCrisisRequest = {}): Promise<TriggerCrisisResponse> {
  const response = await fetch(`${API_BASE_URL}/crisis/trigger`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to trigger crisis: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * React hook for polling crisis status
 */
export function useCrisisStatus(pollInterval: number = 3000) {
  const [status, setStatus] = React.useState<CrisisStatus | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let intervalId: number;

    const fetchStatus = async () => {
      try {
        const crisisStatus = await getCrisisStatus();
        setStatus(crisisStatus);
        setError(null);
      } catch (err) {
        console.error('Error fetching crisis status:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchStatus();

    // Set up polling
    intervalId = window.setInterval(fetchStatus, pollInterval);

    return () => {
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [pollInterval]);

  return { status, loading, error };
}