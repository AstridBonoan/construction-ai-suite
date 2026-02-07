import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { buildApiUrl } from '../config/api';
import styles from './OAuthHandler.module.css';

/**
 * OAuthHandler Component
 * 
 * Handles Monday.com OAuth callback.
 * Receives authorization code/state from Monday.com and exchanges for token.
 * 
 * DEMO DATA: Works with demo OAuth in both authenticated and demo modes.
 */
export default function OAuthHandler() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (!code || !state) {
      setStatus('error');
      setError('Missing authorization code or state');
      setTimeout(() => navigate('/monday/onboard'), 3000);
      return;
    }

    // Exchange code for token with backend
    const exchangeToken = async () => {
      try {
        const response = await fetch(buildApiUrl('/monday/oauth/callback'), {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Token exchange failed');
        }

        // Store tenant info in localStorage
        const tenantId = 'demo_tenant_' + Date.now();
        localStorage.setItem('monday_tenant_id', tenantId);
        localStorage.setItem('monday_authenticated', 'true');
        localStorage.setItem('monday_auth_time', new Date().toISOString());

        setStatus('success');

        // Redirect to dashboard after 1 second
        setTimeout(() => {
          navigate('/monday/dashboard?authenticated=true');
        }, 1000);
      } catch (err: any) {
        setStatus('error');
        setError(err.message);
        setTimeout(() => navigate('/monday/onboard'), 3000);
      }
    };

    exchangeToken();
  }, [searchParams, navigate]);

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        {status === 'processing' && (
          <div className={styles.content}>
            <div className={styles.spinner} />
            <h2>Authorizing with Monday.com</h2>
            <p>Please wait while we complete the authorization process...</p>
          </div>
        )}

        {status === 'success' && (
          <div className={styles.content}>
            <div className={styles.successIcon}>✓</div>
            <h2>Authorization Successful!</h2>
            <p>Your Monday.com account has been connected.</p>
            <p className={styles.subtitle}>Redirecting to dashboard...</p>
          </div>
        )}

        {status === 'error' && (
          <div className={styles.content}>
            <div className={styles.errorIcon}>✕</div>
            <h2>Authorization Failed</h2>
            <p className={styles.error}>{error}</p>
            <p className={styles.subtitle}>Redirecting to setup...</p>
          </div>
        )}
      </div>
    </div>
  );
}
