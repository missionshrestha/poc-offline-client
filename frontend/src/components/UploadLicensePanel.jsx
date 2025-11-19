import React from 'react'

export function UploadLicensePanel() {
  return (
    <div className="panel">
      <h2>Upload / Replace License</h2>
      <p className="panel-description">
        In the next steps, this panel will let you paste or upload a license
        file and send it to the offline backend for installation.
      </p>

      <p style={{ fontSize: '0.85rem', color: '#6b7280' }}>
        For now, this is just a placeholder. The status panel on the left is
        already calling <code>/api/license/status/</code>.
      </p>
    </div>
  )
}
