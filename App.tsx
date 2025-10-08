/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import AgentEdit from './components/AgentEdit';
import ControlTray from './components/console/control-tray/ControlTray';
import ErrorScreen from './components/demo/ErrorSreen';
import KeynoteCompanion from './components/demo/keynote-companion/KeynoteCompanion';
import Header from './components/Header';
import UserSettings from './components/UserSettings';
import { LiveAPIProvider } from './contexts/LiveAPIContext';
import { useUI } from './lib/state';
import Dashboard from './components/dashboard/Dashboard';
import IdeaSubmit from './components/ideas/IdeaSubmit';
import Invitations from './components/assignments/Invitations';
import Marketplace from './components/assignments/Marketplace';
import IdeasAdmin from './components/ideas/IdeasAdmin';

// Resolve Gemini/Live API key from Vite env or process.env (dev/server)
const LIVE_API_KEY =
  (import.meta as any).env?.VITE_GOOGLE_LIVE_API_KEY ??
  (import.meta as any).env?.VITE_GEMINI_API_KEY ??
  (typeof process !== 'undefined'
    ? (process.env as any)?.VITE_GOOGLE_LIVE_API_KEY ??
      (process.env as any)?.VITE_GEMINI_API_KEY ??
      (process.env as any)?.GOOGLE_LIVE_API_KEY ??
      (process.env as any)?.GEMINI_API_KEY
    : undefined);
const HAS_LIVE_API = Boolean(LIVE_API_KEY);
/**
 * Main application component that provides a streaming interface for Live API.
 * Manages video streaming state and provides controls for webcam/screen capture.
 */
function App() {
  const { showUserConfig, showAgentEdit } = useUI();
  return (
    <div className="App">
      <Header />

      {showUserConfig && <UserSettings />}
      {showAgentEdit && <AgentEdit />}
      <IdeaSubmit />
      <Invitations />
      <IdeasAdmin />
      <Marketplace />
      <Dashboard />

      {HAS_LIVE_API ? (
        <LiveAPIProvider apiKey={LIVE_API_KEY as string}>
          <ErrorScreen />
          <div className="streaming-console">
            <main>
              <div className="main-app-area">
                <KeynoteCompanion />
              </div>

              <ControlTray></ControlTray>
            </main>
          </div>
        </LiveAPIProvider>
      ) : (
        <div className="streaming-console">
          <main>
            <div className="main-app-area">
              <div style={{ padding: '1rem', color: '#666' }}>
                Live features disabled. Set VITE_GOOGLE_LIVE_API_KEY (or VITE_GEMINI_API_KEY) to enable streaming console.
              </div>
            </div>
          </main>
        </div>
      )}
    </div>
  );
}

export default App;
