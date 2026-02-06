/**
 * API Configuration
 * Uses VITE_BACKEND_URL environment variable
 * Defaults to http://localhost:5000 for local development
 */

export const getBackendUrl = (): string => {
  return import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';
};

export const buildApiUrl = (path: string): string => {
  const base = getBackendUrl();
  return `${base}${path}`;
};
