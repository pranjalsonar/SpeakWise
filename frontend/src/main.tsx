import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Global tokens/base must load before component CSS so components can override them.
import './index.css'
import { App } from './app/App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
