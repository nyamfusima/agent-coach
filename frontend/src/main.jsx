import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import Admin from './components/Admin.jsx'
import './index.css'

// Lightweight routing: /admin renders the supervisor page, everything else the app.
const isAdmin = window.location.pathname.startsWith('/admin')

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>{isAdmin ? <Admin /> : <App />}</React.StrictMode>,
)
