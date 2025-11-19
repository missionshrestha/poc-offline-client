import React from 'react'
import { LicenseStatusPanel } from './components/LicenseStatusPanel'
import { UploadLicensePanel } from './components/UploadLicensePanel'

function App() {
  return (
    <div className="app-root">
      <header className="app-header">
        <h1>Offline Data Pipeline – License Console</h1>
        <p className="app-subtitle">
          This UI is running fully offline and validates a signed license file.
        </p>
      </header>

      <main className="app-main">
        <section className="app-main-left">
          <LicenseStatusPanel />
        </section>
        <section className="app-main-right">
          <UploadLicensePanel />
        </section>
      </main>
    </div>
  )
}

export default App
