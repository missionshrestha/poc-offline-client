import React, { useEffect, useState } from 'react'
import { fetchLicenseStatus } from '../api/licenseApi'

export function LicenseStatusPanel() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let isMounted = true

    async function loadStatus() {
      setLoading(true)
      setError(null)
      try {
        const data = await fetchLicenseStatus()
        if (isMounted) {
          setStatus(data)
        }
      } catch (err) {
        if (isMounted) {
          setError(err)
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadStatus()

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <div className="panel">
      <h2>License Status</h2>
      <p className="panel-description">
        Current license status as reported by the offline backend.
      </p>

      {loading && <p>Loading...</p>}
      {error && (
        <p style={{ color: '#b91c1c' }}>
          Failed to load status: {error.message}
        </p>
      )}

      {!loading && !error && status && (
        <pre style={{
          background: '#f3f4f6',
          borderRadius: '0.5rem',
          padding: '0.75rem',
          fontSize: '0.8rem',
          overflowX: 'auto',
        }}>
{JSON.stringify(status, null, 2)}
        </pre>
      )}

      {!loading && !error && !status && (
        <p>No status data yet.</p>
      )}
    </div>
  )
}
