import React, { useState, useEffect } from 'react';
import styles from './MondayOnboarding.module.css';

/**
 * MondayOnboarding Component
 * 
 * Onboarding flow for Monday.com integration:
 * 1. Welcome screen with auth button
 * 2. Board selection (after OAuth)
 * 3. Sync configuration
 * 4. Demo data preview
 * 
 * DEMO DATA: Works in demo mode with synthetic boards/items.
 */
export default function MondayOnboarding() {
  const [step, setStep] = useState<'welcome' | 'authorize' | 'boards' | 'config' | 'success'>('welcome');
  const [boards, setBoards] = useState<any[]>([]);
  const [selectedBoard, setSelectedBoard] = useState<string | null>(null);
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncConfig, setSyncConfig] = useState({
    syncTasks: true,
    syncBudgets: true,
    syncSchedule: true,
    pushRiskScores: false,
  });

  const tenantId = localStorage.getItem('monday_tenant_id') || 'demo_tenant_' + Date.now();
  const isAuthenticated = localStorage.getItem('monday_authenticated') === 'true';

  // Step 1: Welcome
  const handleInitiateAuth = () => {
    setLoading(true);
    // Call backend to get auth URL
    fetch(`http://localhost:5000/monday/oauth/init?tenant_id=${tenantId}`)
      .then((res) => res.json())
      .then((data) => {
        localStorage.setItem('monday_tenant_id', tenantId);
        window.location.href = data.auth_url;
      })
      .catch((err) => {
        setError(`Auth failed: ${err.message}`);
        setLoading(false);
      });
  };

  // Step 2: Boards selection (after OAuth or in demo mode)
  useEffect(() => {
    // Load boards when entering board selection step, regardless of authentication status
    // (demo mode doesn't require authentication)
    if (step === 'boards') {
      loadBoards();
    }
  }, [step]);

  const loadBoards = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:5000/monday/boards?tenant_id=${tenantId}`
      );
      const data = await response.json();
      setBoards(data.boards || []);
      setError(null);
    } catch (err: any) {
      setError(`Failed to load boards: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleBoardSelect = async (boardId: string) => {
    console.log(`[DEBUG] Board selected: ${boardId}`);
    setSelectedBoard(boardId);
    setLoading(true);

    try {
      const response = await fetch(
        `http://localhost:5000/monday/boards/${boardId}/items?tenant_id=${tenantId}`
      );
      const data = await response.json();
      setItems(data.items || []);
      setError(null);
    } catch (err: any) {
      setError(`Failed to load items: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStartSync = async () => {
    if (!selectedBoard) {
      setError('Please select a board');
      return;
    }

    setLoading(true);
    try {
      // Configure sync
      await fetch('http://localhost:5000/monday/sync/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: tenantId,
          board_id: selectedBoard,
          project_name: boards.find((b) => b.id === selectedBoard)?.name || 'Project',
        }),
      });

      // Start sync
      const syncResponse = await fetch('http://localhost:5000/monday/sync/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: tenantId,
          board_id: selectedBoard,
        }),
      });

      if (syncResponse.ok) {
        setStep('success');
      } else {
        setError('Sync start failed');
      }
    } catch (err: any) {
      setError(`Setup failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.panel}>
        {/* Step 1: Welcome */}
        {step === 'welcome' && (
          <div className={styles.step}>
            <div className={styles.icon}>📅</div>
            <h1>Connect to Monday.com</h1>
            <p>Integrate AI Construction Suite with your Monday.com workspace for seamless project insights.</p>

            <div className={styles.features}>
              <div className={styles.feature}>
                <span className={styles.checkmark}>✓</span>
                <span>Real-time task sync</span>
              </div>
              <div className={styles.feature}>
                <span className={styles.checkmark}>✓</span>
                <span>AI risk predictions</span>
              </div>
              <div className={styles.feature}>
                <span className={styles.checkmark}>✓</span>
                <span>Schedule impact analysis</span>
              </div>
              <div className={styles.feature}>
                <span className={styles.checkmark}>✓</span>
                <span>Delay probability forecasts</span>
              </div>
            </div>

            <button className={styles.primary} onClick={handleInitiateAuth} disabled={loading}>
              {loading ? 'Redirecting...' : 'Authorize with Monday.com'}
            </button>

            <p className={styles.note}>
              Demo Mode: You can also explore with demo data without authorization.
            </p>
            <button className={styles.secondary} onClick={() => setStep('boards')}>
              Continue in Demo Mode
            </button>
          </div>
        )}

        {/* Step 2: Board Selection */}
        {step === 'boards' && (
          <div className={styles.step}>
            <h1>Select a Board</h1>
            <p>Choose which Monday.com board to integrate with AI Construction Suite.</p>

            {error && <div className={styles.error}>{error}</div>}

            {loading ? (
              <div className={styles.loading}>Loading boards...</div>
            ) : (
              <div className={styles.boardList}>
                {boards.length === 0 ? (
                  <p className={styles.empty}>No boards found. Please authorize first.</p>
                ) : (
                  boards.map((board, idx) => (
                    <button
                      key={board.id}
                      className={`${styles.boardCard} ${selectedBoard === board.id ? styles.selected : ''}`}
                      onClick={() => handleBoardSelect(board.id)}
                      data-testid={`board-card-${idx}`}
                      style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', width: '100%', textAlign: 'left' }}
                    >
                      <h3>{board.name}</h3>
                      <p>{board.description || 'No description'}</p>
                      <div className={styles.meta}>
                        <span>{board.groups || 0} groups</span>
                        <span>{board.items || 0} items</span>
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}

            {selectedBoard && (
              <>
                <h3>Preview Items ({items.length})</h3>
                <div className={styles.itemPreview}>
                  {items.slice(0, 3).map((item, idx) => (
                    <div key={idx} className={styles.item}>
                      <div className={styles.itemName}>{item.name}</div>
                      <div className={styles.itemStatus}>{item.status}</div>
                    </div>
                  ))}
                  {items.length > 3 && <div className={styles.more}>+{items.length - 3} more</div>}
                </div>
              </>
            )}

            {/* Next button enables when at least one board is selected */}
            <button
              className={styles.primary}
              onClick={() => setStep('config')}
              disabled={!selectedBoard}
              data-testid="next-configure-sync-btn"
            >
              Next: Configure Sync
            </button>
            <button className={styles.secondary} onClick={() => setStep('welcome')}>
              Back
            </button>
          </div>
        )}

        {/* Step 3: Sync Configuration */}
        {step === 'config' && (
          <div className={styles.step}>
            <h1>Configure Sync</h1>
            <p>Select what data to sync from Monday.com to Construction Suite.</p>

            <div className={styles.configOptions}>
              <label className={styles.checkbox}>
                <input
                  type="checkbox"
                  checked={syncConfig.syncTasks}
                  onChange={(e) => setSyncConfig({ ...syncConfig, syncTasks: e.target.checked })}
                />
                <span>Sync Tasks & Assignments</span>
              </label>
              <label className={styles.checkbox}>
                <input
                  type="checkbox"
                  checked={syncConfig.syncBudgets}
                  onChange={(e) => setSyncConfig({ ...syncConfig, syncBudgets: e.target.checked })}
                />
                <span>Sync Budget & Cost Data</span>
              </label>
              <label className={styles.checkbox}>
                <input
                  type="checkbox"
                  checked={syncConfig.syncSchedule}
                  onChange={(e) => setSyncConfig({ ...syncConfig, syncSchedule: e.target.checked })}
                />
                <span>Sync Schedule & Dates</span>
              </label>
              <label className={styles.checkbox}>
                <input
                  type="checkbox"
                  checked={syncConfig.pushRiskScores}
                  onChange={(e) => setSyncConfig({ ...syncConfig, pushRiskScores: e.target.checked })}
                />
                <span>Push Risk Scores & Alerts Back to Monday</span>
              </label>
            </div>

            <div className={styles.infoBox}>
              <p>
                <strong>Demo Mode:</strong> Data sync will use synthetic data from our database.
                No real Monday.com API calls are made.
              </p>
            </div>

            <button className={styles.primary} onClick={handleStartSync} disabled={loading}>
              {loading ? 'Setting up...' : 'Start Integration'}
            </button>
            <button className={styles.secondary} onClick={() => setStep('boards')}>
              Back
            </button>
          </div>
        )}

        {/* Step 4: Success */}
        {step === 'success' && (
          <div className={styles.step}>
            <div className={styles.successIcon}>✓</div>
            <h1>Integration Complete!</h1>
            <p>Your Monday.com board is now synced with AI Construction Suite.</p>

            <div className={styles.successDetails}>
              <div className={styles.detail}>
                <strong>Board:</strong> {boards.find((b) => b.id === selectedBoard)?.name || 'Selected'}
              </div>
              <div className={styles.detail}>
                <strong>Items Synced:</strong> {items.length} tasks
              </div>
              <div className={styles.detail}>
                <strong>Status:</strong> <span className={styles.active}>Active</span>
              </div>
            </div>

            <p className={styles.note}>
              Your AI Construction Suite dashboard now has access to real-time Monday.com data.
            </p>

            <button className={styles.primary} onClick={() => (window.location.href = '/monday/dashboard')}>
              Go to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
