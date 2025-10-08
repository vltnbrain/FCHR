import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { LiveAPIProvider } from '../../contexts/LiveAPIContext'

const liveApiKey = import.meta.env.VITE_GOOGLE_LIVE_API_KEY as string | undefined

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {liveApiKey ? (
      <LiveAPIProvider apiKey={liveApiKey}>
        <App />
      </LiveAPIProvider>
    ) : (
      <App />
    )}
  </React.StrictMode>,
)
