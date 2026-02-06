/*
Phase 17: Monday.com Frontend OAuth Integration

Client-side component for seamless Monday.com OAuth without manual API key entry.
*/

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const MondayOAuthComponent = () => {
  const [status, setStatus] = useState('idle'); // idle, connecting, authenticated, error
  const [userInfo, setUserInfo] = useState(null);
  const [boards, setBoards] = useState([]);
  const [selectedBoard, setSelectedBoard] = useState(null);
  const [message, setMessage] = useState('');

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get('/api/monday/status');
      if (response.data.authenticated_workspaces.length > 0) {
        setStatus('authenticated');
      }
    } catch {
      console.log('Not authenticated yet');
    }
  };

  // Check if already authenticated
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Initiate OAuth flow
  const handleConnectMonday = async () => {
    setStatus('connecting');
    try {
      const response = await axios.get('/api/monday/oauth/start');
      if (response.data.authorization_url) {
        // Redirect to Monday.com OAuth
        window.location.href = response.data.authorization_url;
      }
    } catch (error) {
      setStatus('error');
      setMessage(`Failed to initiate connection: ${error.message}`);
    }
  };

  // Load user's boards
  const _loadUserBoards = async () => {
    try {
      const response = await axios.get('/api/monday/sync/boards');
      setUserInfo(response.data.user);
      setBoards(response.data.boards);
      setStatus('authenticated');
    } catch (error) {
      setMessage(`Failed to load boards: ${error.message}`);
    }
  };

  // Sync and analyze selected board
  const handleAnalyzeBoard = async () => {
    if (!selectedBoard) {
      setMessage('Please select a board');
      return;
    }

    try {
      setMessage(`Analyzing ${selectedBoard.name}...`);
      const response = await axios.post(
        `/api/monday/sync/analyze/${selectedBoard.id}`
      );
      setMessage(response.data.message);
    } catch (error) {
      setMessage(`Analysis failed: ${error.message}`);
    }
  };

  // UI Components
  if (status === 'idle' || status === 'error') {
    return (
      <div className="monday-oauth-panel">
        <h2>Connect to Monday.com</h2>
        <p>Link your Monday.com boards to unlock construction AI features:</p>
        <ul>
          <li>Automatic schedule analysis</li>
          <li>Risk identification and scoring</li>
          <li>Smart recommendations</li>
          <li>Real-time sync with your tasks</li>
        </ul>
        <button 
          onClick={handleConnectMonday}
          className="btn-monday-oauth"
        >
          🔗 Connect Monday.com
        </button>
        {message && <p className="error">{message}</p>}
      </div>
    );
  }

  if (status === 'connecting') {
    return (
      <div className="loading">
        <p>Redirecting to Monday.com...</p>
      </div>
    );
  }

  // Authenticated state - show boards
  return (
    <div className="monday-authenticated-panel">
      <h2>Monday.com Connected</h2>
      {userInfo && (
        <p>Connected as: <strong>{userInfo.name}</strong> ({userInfo.email})</p>
      )}

      <h3>Your Boards</h3>
      <select 
        value={selectedBoard?.id || ''}
        onChange={(e) => {
          const board = boards.find(b => b.id === e.target.value);
          setSelectedBoard(board);
        }}
        className="board-selector"
      >
        <option value="">Select a board...</option>
        {boards.map(board => (
          <option key={board.id} value={board.id}>
            {board.name}
          </option>
        ))}
      </select>

      {selectedBoard && (
        <div className="board-actions">
          <p>Selected: <strong>{selectedBoard.name}</strong></p>
          <button 
            onClick={handleAnalyzeBoard}
            className="btn-analyze"
          >
            📊 Analyze Schedule
          </button>
        </div>
      )}

      {message && <p className="info">{message}</p>}
    </div>
  );
};

export default MondayOAuthComponent;


// CSS Styles (for reference, inject via <style> tag as needed)
const _styles = `
.monday-oauth-panel {
  padding: 20px;
  border: 2px solid #0073ea;
  border-radius: 8px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8f0f7 100%);
}

.monday-oauth-panel h2 {
  color: #0073ea;
  margin-top: 0;
}

.monday-oauth-panel ul {
  list-style: none;
  padding: 0;
}

.monday-oauth-panel li {
  padding: 8px 0;
  padding-left: 20px;
  position: relative;
}

.monday-oauth-panel li:before {
  content: "✓";
  position: absolute;
  left: 0;
  color: #00c96e;
  font-weight: bold;
}

.btn-monday-oauth {
  background: linear-gradient(135deg, #0073ea 0%, #0057b8 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-monday-oauth:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 115, 234, 0.3);
}

.monday-authenticated-panel {
  padding: 20px;
  border: 2px solid #00c96e;
  border-radius: 8px;
  background: linear-gradient(135deg, #f5faf7 0%, #e8f7f0 100%);
}

.board-selector {
  width: 100%;
  padding: 10px;
  border: 1px solid #0073ea;
  border-radius: 6px;
  font-size: 14px;
  margin: 10px 0;
}

.board-actions {
  margin-top: 15px;
  padding: 15px;
  background: white;
  border-radius: 6px;
  border-left: 4px solid #0073ea;
}

.btn-analyze {
  background: #00c96e;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-analyze:hover {
  background: #00b85c;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #0073ea;
}

.error {
  color: #e41e2d;
  padding: 10px;
  background: #ffe8e8;
  border-radius: 6px;
  margin-top: 10px;
}

.info {
  color: #0073ea;
  padding: 10px;
  background: #e8f0f7;
  border-radius: 6px;
  margin-top: 10px;
}
`;
