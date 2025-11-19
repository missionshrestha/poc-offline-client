import React from 'react'
import { useLicense } from '../context/LicenseContext'

export function LicenseStatusPanel() {
  const { license, loading, error, refreshLicenseStatus } = useLicense()

  return (
    <div className="panel">
      <h2>License Status</h2>
      <p className="panel-description">
        Current license status as reported by the offline backend.
      </p>

      <div style={{ marginBottom: '0.75rem' }}>
        <button
          type="button"
          onClick={refreshLicenseStatus}
          style={{
            padding: '0.3rem 0.7rem',
            fontSize: '0.8rem',
            borderRadius: '999px',
            border: '1px solid #d1d5db',
            backgroundColor: '#f9fafb',
            cursor: 'pointer',
          }}
        >
          Refresh status
        </button>
      </div>

      {loading && <p>Loading...</p>}

      {error && (
        <p style={{ color: '#b91c1c', fontSize: '0.9rem' }}>
          Failed to load status: {error.message}
        </p>
      )}

      {!loading && !error && !license && (
        <p>No license information available.</p>
      )}

      {!loading && !error && license && (
        <>
          <div style={{ marginBottom: '0.75rem', fontSize: '0.9rem' }}>
            <strong>Status:</strong>{' '}
            <span
              style={{
                padding: '0.15rem 0.45rem',
                borderRadius: '999px',
                fontSize: '0.8rem',
                textTransform: 'uppercase',
                letterSpacing: '0.03em',
                backgroundColor: license.isValid ? '#dcfce7' : '#fee2e2',
                color: license.isValid ? '#166534' : '#b91c1c',
              }}
            >
              {license.status}
            </span>
          </div>

          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.9rem' }}>
            <li><strong>Customer:</strong> {license.customerName || '—'}</li>
            <li><strong>Edition:</strong> {license.editionName || license.editionCode || '—'}</li>
            <li><strong>Type:</strong> {license.licenseType || '—'}</li>
            <li><strong>License ID:</strong> {license.licenseId || '—'}</li>
            <li><strong>Valid from:</strong> {license.validFrom || '—'}</li>
            <li><strong>Valid until:</strong> {license.validUntil || '—'}</li>
          </ul>

          {license.warnings && license.warnings.length > 0 && (
            <div
              style={{
                marginTop: '0.75rem',
                padding: '0.5rem 0.75rem',
                borderRadius: '0.5rem',
                backgroundColor: '#fffbeb',
                border: '1px solid #fbbf24',
                fontSize: '0.8rem',
              }}
            >
              <strong>Warnings:</strong>
              <ul style={{ paddingLeft: '1.1rem', marginTop: '0.3rem' }}>
                {license.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <details
            style={{
              marginTop: '0.75rem',
              fontSize: '0.8rem',
            }}
          >
            <summary>Raw normalized license object</summary>
            <pre
              style={{
                background: '#f3f4f6',
                borderRadius: '0.5rem',
                padding: '0.75rem',
                marginTop: '0.4rem',
                fontSize: '0.75rem',
                overflowX: 'auto',
              }}
            >
{JSON.stringify(license, null, 2)}
            </pre>
          </details>
        </>
      )}
    </div>
  )
}
