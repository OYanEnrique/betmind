/**
 * BetMind Frontend Application Logic
 * Pure Client-Server architecture connecting to local FastAPI agent.
 * Respects Material Design 3 guidelines. No emojis.
 */

// Application State
const state = {
  fastApiUrl: localStorage.getItem('betmind_api_url') || 'http://localhost:8000',
  userId: localStorage.getItem('betmind_user_id') || '',
  sessionId: localStorage.getItem('betmind_session_id') || '',
  resiliencePoints: 0,
  userRole: 'guest',
  activeProtocols: {
    BREATHE478: true,
    DISTRACT5M: true
  },
  theme: localStorage.getItem('betmind_theme') || 'dark',
  isStreaming: false,
  isConnected: false
};

// UI Element Selections
const elements = {
  hamburgerBtn: document.getElementById('hamburger-btn'),
  sidebar: document.getElementById('sidebar'),
  sidebarOverlay: document.getElementById('sidebar-overlay'),
  themeToggleBtn: document.getElementById('theme-toggle-btn'),
  themeIcon: document.getElementById('theme-icon'),
  apiUrlInput: document.getElementById('api-url-input'),
  reconnectBtn: document.getElementById('reconnect-btn'),
  connectionDot: document.getElementById('connection-dot'),
  connectionText: document.getElementById('connection-text'),
  userIdInput: document.getElementById('user-id-input'),
  registerBtn: document.getElementById('register-btn'),
  pointsCounter: document.getElementById('points-counter'),
  userRoleLabel: document.getElementById('user-role-label'),
  activeUserDisplay: document.getElementById('active-user-display'),
  breatheSwitch: document.getElementById('protocol-breathe-switch'),
  distractSwitch: document.getElementById('protocol-distract-switch'),
  chatMessages: document.getElementById('chat-messages'),
  chatEmptyState: document.getElementById('chat-empty-state'),
  chatForm: document.getElementById('chat-form'),
  chatInputField: document.getElementById('chat-input-field'),
  chipsContainer: document.getElementById('chips-container')
};

// SVG Paths for Dark/Light theme icons
const themeIcons = {
  dark: `<path d="M12 3c.132 0 .263 0 .393.007a7.5 7.5 0 0 0 7.92 12.446A9 9 0 1 1 12 3zm0 2a7 7 0 1 0 0 14 7 7 0 0 0 0-14z"/>`,
  light: `<path d="M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM2 13h2a1 1 0 0 0 0-2H2a1 1 0 0 0 0 2zm18 0h2a1 1 0 0 0 0-2h-2a1 1 0 0 0 0 2zM11 2v2a1 1 0 0 0 2 0V2a1 1 0 0 0-2 0zm0 18v2a1 1 0 0 0 2 0v-2a1 1 0 0 0-2 0zM5.99 4.58a1 1 0 1 0-1.41 1.41l1.06 1.06a1 1 0 0 0 1.41-1.41L5.99 4.58zm12.37 12.37a1 1 0 1 0-1.41 1.41l1.06 1.06a1 1 0 0 0 1.41-1.41l-1.06-1.06zm-12.37 1.06a1 1 0 0 0 0 1.41l1.06-1.06a1 1 0 1 0-1.41-1.41l-1.06 1.06zm13.43-13.43a1 1 0 0 0-1.41 0l-1.06 1.06a1 1 0 1 0 1.41 1.41l1.06-1.06a1 1 0 0 0 0-1.41z"/>`
};

// Initialize Application
async function init() {
  setupTheme();
  setupEventListeners();
  applyStateInputs();
  await checkBackendConnection();
  if (state.isConnected && state.userId && state.sessionId) {
    await syncSessionState();
  }
}

// Setup visual appearance (Light / Dark mode)
function setupTheme() {
  document.documentElement.setAttribute('data-theme', state.theme);
  updateThemeIcon();
}

function updateThemeIcon() {
  if (state.theme === 'light') {
    elements.themeIcon.innerHTML = themeIcons.light;
  } else {
    elements.themeIcon.innerHTML = themeIcons.dark;
  }
}

function toggleTheme() {
  state.theme = state.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('betmind_theme', state.theme);
  setupTheme();
}

// Populate input values from localStorage state
function applyStateInputs() {
  elements.apiUrlInput.value = state.fastApiUrl;
  elements.userIdInput.value = state.userId;
  if (state.userId) {
    elements.activeUserDisplay.innerText = `Active ID: ${state.userId}`;
  }
}

// Bind DOM event listeners
function setupEventListeners() {
  // Mobile Hamburger menu drawer toggles
  elements.hamburgerBtn.addEventListener('click', toggleSidebar);
  elements.sidebarOverlay.addEventListener('click', closeSidebar);
  
  // Theme toggle button
  elements.themeToggleBtn.addEventListener('click', toggleTheme);
  
  // Reconnect server button
  elements.reconnectBtn.addEventListener('click', async () => {
    const originalText = elements.reconnectBtn.innerText;
    elements.reconnectBtn.innerText = 'Connecting...';
    elements.reconnectBtn.disabled = true;
    
    state.fastApiUrl = elements.apiUrlInput.value.trim();
    localStorage.setItem('betmind_api_url', state.fastApiUrl);
    
    const isSuccess = await checkBackendConnection();
    
    elements.reconnectBtn.innerText = originalText;
    elements.reconnectBtn.disabled = false;
    
    if (isSuccess) {
      appendSystemMessage(`Successfully connected to backend server at ${state.fastApiUrl}`);
    } else {
      appendSystemMessage(`Failed to connect to backend server at ${state.fastApiUrl}`);
    }
  });
  
  // Register user button
  elements.registerBtn.addEventListener('click', async () => {
    const inputId = elements.userIdInput.value.trim();
    if (!inputId) {
      alert('Please enter a valid User ID.');
      return;
    }
    await registerUserSession(inputId);
  });
  
  // Chat submit form
  elements.chatForm.addEventListener('submit', handleChatSubmit);
  
  // Suggestion chips clicks
  elements.chipsContainer.addEventListener('click', (e) => {
    const chip = e.target.closest('.suggestion-chip');
    if (!chip) return;
    
    const message = chip.getAttribute('data-msg');
    if (message) {
      sendChatMessage(message);
    }
  });

  // Admin Toggles
  elements.breatheSwitch.addEventListener('change', (e) => handleProtocolToggle('BREATHE478', e.target.checked));
  elements.distractSwitch.addEventListener('change', (e) => handleProtocolToggle('DISTRACT5M', e.target.checked));
}

// Toggle drawer menu in mobile layout
function toggleSidebar() {
  elements.sidebar.classList.toggle('active');
  elements.sidebarOverlay.classList.toggle('active');
  elements.hamburgerBtn.classList.toggle('active');
}

function closeSidebar() {
  elements.sidebar.classList.remove('active');
  elements.sidebarOverlay.classList.remove('active');
  elements.hamburgerBtn.classList.remove('active');
}

// Check server connection status using the API health endpoint
async function checkBackendConnection() {
  updateConnectionStatus('checking');
  try {
    // Fetch using no-cors mode to verify server state without CORS blocking
    await fetch(`${state.fastApiUrl}/health`, { method: 'GET', mode: 'no-cors' });
    state.isConnected = true;
    updateConnectionStatus('connected');
    return true;
  } catch (error) {
    state.isConnected = false;
    updateConnectionStatus('disconnected');
    console.error('Server connection failure:', error);
    return false;
  }
}

function updateConnectionStatus(status) {
  elements.connectionDot.className = 'status-dot';
  if (status === 'connected') {
    elements.connectionDot.classList.add('connected');
    elements.connectionText.innerText = 'Connected to Server';
  } else if (status === 'disconnected') {
    elements.connectionDot.classList.add('disconnected');
    elements.connectionText.innerText = 'Server Offline';
  } else {
    elements.connectionText.innerText = 'Verifying connection...';
  }
}

// Register user session with backend
async function registerUserSession(userId) {
  if (!state.isConnected) {
    alert('Cannot register. The backend server is offline.');
    return;
  }
  
  try {
    const sessionUrl = `${state.fastApiUrl}/apps/app/users/${userId}/sessions`;
    const response = await fetch(sessionUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: { preferred_language: 'English' } })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    state.userId = userId;
    state.sessionId = data.id;
    
    localStorage.setItem('betmind_user_id', userId);
    localStorage.setItem('betmind_session_id', data.id);
    
    elements.activeUserDisplay.innerText = `Active ID: ${userId}`;
    appendSystemMessage('Session successfully registered on server.');
    
    await syncSessionState();
  } catch (error) {
    console.error('Registration failed:', error);
    alert('Failed to register user session with backend server.');
  }
}

// Sync local states from the backend session resource
async function syncSessionState() {
  if (!state.isConnected || !state.userId || !state.sessionId) return;
  
  try {
    const sessionUrl = `${state.fastApiUrl}/apps/app/users/${state.userId}/sessions/${state.sessionId}`;
    const response = await fetch(sessionUrl, { method: 'GET' });
    
    if (response.status === 404) {
      // Session has expired or cleared on server
      state.sessionId = '';
      localStorage.removeItem('betmind_session_id');
      elements.pointsCounter.innerText = '0';
      elements.userRoleLabel.innerText = 'Role: Guest';
      disableAdminControls();
      return;
    }
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const data = await response.json();
    const sessionState = data.state || {};
    
    // Parse resilience points from state
    state.resiliencePoints = sessionState.resilience_points || 0;
    elements.pointsCounter.innerText = state.resiliencePoints;
    
    // Parse user role (check admin privileges)
    state.userRole = sessionState.user_role || 'guest';
    elements.userRoleLabel.innerText = `Role: ${state.userRole.charAt(0).toUpperCase() + state.userRole.slice(1)}`;
    
    // Parse active protocols
    state.activeProtocols.BREATHE478 = sessionState['app:active_protocol:BREATHE478'] !== false;
    state.activeProtocols.DISTRACT5M = sessionState['app:active_protocol:DISTRACT5M'] !== false;
    
    // Update admin switch UI controls
    updateAdminControlsUI();
  } catch (error) {
    console.error('Session sync error:', error);
  }
}

function updateAdminControlsUI() {
  const isAdmin = state.userRole === 'admin';
  
  elements.breatheSwitch.disabled = !isAdmin;
  elements.distractSwitch.disabled = !isAdmin;
  
  elements.breatheSwitch.checked = state.activeProtocols.BREATHE478;
  elements.distractSwitch.checked = state.activeProtocols.DISTRACT5M;
}

function disableAdminControls() {
  elements.breatheSwitch.disabled = true;
  elements.distractSwitch.disabled = true;
  elements.breatheSwitch.checked = false;
  elements.distractSwitch.checked = false;
}

// Modify protocol active status via session patch (Admin Action)
async function handleProtocolToggle(protocolCode, isChecked) {
  if (!state.isConnected || !state.userId || !state.sessionId) return;
  
  try {
    const sessionUrl = `${state.fastApiUrl}/apps/app/users/${state.userId}/sessions/${state.sessionId}`;
    const patchBody = {
      state: {
        [`app:active_protocol:${protocolCode}`]: isChecked
      }
    };
    
    const response = await fetch(sessionUrl, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patchBody)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    state.activeProtocols[protocolCode] = isChecked;
    appendSystemMessage(`Protocol ${protocolCode} status updated to ${isChecked ? 'active' : 'inactive'}.`);
  } catch (error) {
    console.error('Failed to patch protocol status:', error);
    alert('Authorization failed or server failed to update protocol status.');
    // Revert UI check state
    updateAdminControlsUI();
  }
}

// Handle Form Submission
function handleChatSubmit(e) {
  e.preventDefault();
  const inputMessage = elements.chatInputField.value.trim();
  if (!inputMessage) return;
  sendChatMessage(inputMessage);
}

// Main conversation workflow
async function sendChatMessage(messageText) {
  if (state.isStreaming) return;
  
  // Clear input field immediately
  elements.chatInputField.value = '';
  
  // Enforce Registration before conversation starts
  if (!state.userId) {
    appendUserBubble(messageText);
    appendAgentBubble('Please enter a User ID and click Register Session in the sidebar before talking with BetMind.');
    return;
  }
  
  // Lazy session creation if not created yet
  if (!state.sessionId) {
    await registerUserSession(state.userId);
    if (!state.sessionId) return;
  }
  
  // UI adjustment: Remove empty state placeholder
  if (elements.chatEmptyState) {
    elements.chatEmptyState.remove();
  }
  
  // Append User Message Bubble
  appendUserBubble(messageText);
  
  // Append Agent Message Bubble with Streaming Indicator
  const agentBubble = createAgentBubblePlaceholder();
  const contentWrapper = agentBubble.querySelector('.message-content');
  
  state.isStreaming = true;
  scrollChatToBottom();
  
  try {
    const sseUrl = `${state.fastApiUrl}/run_sse`;
    const response = await fetch(sseUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        app_name: 'app',
        user_id: state.userId,
        session_id: state.sessionId,
        new_message: {
          role: 'user',
          parts: [{ text: messageText }]
        },
        streaming: true
      })
    });
    
    if (!response.ok) {
      let errorText = '';
      try {
        errorText = await response.text();
      } catch (e) {}
      
      if (response.status === 429 || errorText.includes('RESOURCE_EXHAUSTED') || errorText.includes('Too Many Requests') || errorText.includes('quota')) {
        throw new Error('API Rate Limit Exceeded: You have exceeded the free tier quota for the Gemini API. Please wait 20-30 seconds before retrying.');
      }
      throw new Error(`HTTP ${response.status}: ${errorText || 'Server Error'}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let responseText = '';
    let accumulatedDelta = '';
    
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep partial line in buffer
      
      for (const line of lines) {
        const cleanLine = line.trim();
        if (cleanLine.startsWith('data: ')) {
          try {
            const eventData = JSON.parse(cleanLine.slice(6));
            if (eventData && eventData.content && eventData.content.parts) {
              const eventText = eventData.content.parts.map(p => p.text || '').join('');
              if (eventData.partial === false) {
                // If it is the final consolidated message, overwrite responseText to avoid duplication (only if not empty)
                if (eventText.trim() !== '') {
                  responseText = eventText;
                }
              } else {
                // Accumulate incremental chunks
                accumulatedDelta += eventText;
                responseText = accumulatedDelta;
              }
              contentWrapper.innerHTML = formatMarkdown(responseText) + (eventData.partial !== false ? getStreamingIndicatorHTML() : '');
              scrollChatToBottom();
            }
          } catch (e) {
            // Partial or metadata line parsing issues ignored silently
          }
        }
      }
    }
    
    // Render final text, remove loading dots indicator
    if (!responseText.trim()) {
      responseText = '<span style="color: var(--accent-error);">The agent did not respond. This is typically caused by Gemini API rate limits (quota exhausted on the free tier) or a server exception. Please wait 20-30 seconds and try again, or check your backend terminal logs.</span>';
      contentWrapper.innerHTML = responseText;
    } else {
      contentWrapper.innerHTML = formatMarkdown(responseText);
    }
    
  } catch (error) {
    console.error('Chat error:', error);
    if (error.message.includes('API Rate Limit Exceeded')) {
      contentWrapper.innerHTML = `<span style="color: var(--accent-error);">${escapeHTML(error.message)}</span>`;
    } else {
      contentWrapper.innerHTML = '<span style="color: var(--accent-error);">Server connection error. Make sure the local FastAPI server is running on port 8000 and has ALLOW_ORIGINS enabled.</span>';
    }
  } finally {
    state.isStreaming = false;
    scrollChatToBottom();
    // Fetch updated points/status details from server after turn is completed
    await syncSessionState();
  }
}

// UI Rendering Helpers
function appendUserBubble(text) {
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble user';
  bubble.innerHTML = `<div class="message-content">${escapeHTML(text)}</div>`;
  elements.chatMessages.appendChild(bubble);
  scrollChatToBottom();
}

function createAgentBubblePlaceholder() {
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble agent';
  bubble.innerHTML = `<div class="message-content">${getStreamingIndicatorHTML()}</div>`;
  elements.chatMessages.appendChild(bubble);
  return bubble;
}

function appendAgentBubble(text) {
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble agent';
  bubble.innerHTML = `<div class="message-content">${formatMarkdown(text)}</div>`;
  elements.chatMessages.appendChild(bubble);
  scrollChatToBottom();
}

function appendSystemMessage(text) {
  const msg = document.createElement('div');
  msg.style.alignSelf = 'center';
  msg.style.fontSize = '11px';
  msg.style.color = 'var(--text-secondary)';
  msg.style.backgroundColor = 'var(--bg-input)';
  msg.style.padding = '4px 10px';
  msg.style.borderRadius = '100px';
  msg.style.border = '1px solid var(--border-color)';
  msg.style.marginTop = '4px';
  msg.innerText = text;
  elements.chatMessages.appendChild(msg);
  scrollChatToBottom();
}

function getStreamingIndicatorHTML() {
  return `
    <span class="streaming-indicator">
      <span class="streaming-dot"></span>
      <span class="streaming-dot"></span>
      <span class="streaming-dot"></span>
    </span>
  `;
}

function scrollChatToBottom() {
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// Helper to escape HTML characters
function escapeHTML(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// A simple Markdown regex parser for safe styling rendering
function formatMarkdown(markdownText) {
  let html = escapeHTML(markdownText);

  // Line breaks to <br>
  html = html.replace(/\n/g, '<br>');

  // Bold (**text** -> <strong>text</strong>)
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Bullet items (e.g. * Item or - Item)
  // Match start of line or <br> followed by optional whitespace and star/dash
  html = html.replace(/(?:^|<br>)\s*[\*\-]\s+([^<]+)/g, (match, p1) => {
    return `<br><span style="padding-left: 12px; display: inline-block;">&bull; ${p1}</span>`;
  });

  return html;
}

// Launch application
window.addEventListener('DOMContentLoaded', init);
