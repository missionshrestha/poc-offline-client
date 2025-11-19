import React from 'react'
import { useLicense } from '../context/LicenseContext'

export function FeatureGatingDemo() {
  const { license, canUse } = useLicense()

  const hasPipelineExecution = canUse('pipeline_execution')
  const hasAdvancedExport = canUse('advanced_export')
  const hasCustomConnectors = canUse('custom_connectors')

  function disabledReason(featureKey, allowed) {
    if (allowed) return null

    if (!license) {
      return 'No license installed'
    }

    if (!license.isValid) {
      return `License status: ${license.status}`
    }

    return `Feature '${featureKey}' is not granted in this license`
  }

  function handleDummyClick(actionLabel) {
    // This is just a demo hook; later we will wire real endpoints.
    window.alert(`(Demo) This would trigger: ${actionLabel}`)
  }

  return (
    <div className="panel" style={{ marginTop: '1rem' }}>
      <h2>Feature Gating Demo</h2>
      <p className="panel-description">
        These actions are enabled or disabled based on the license status and
        feature flags returned by the offline backend.
      </p>

      <div
        style={{
          marginBottom: '0.75rem',
          fontSize: '0.9rem',
        }}
      >
        <strong>Edition:</strong>{' '}
        {license
          ? (license.editionName || license.editionCode || '—')
          : '—'}
        <br />
        <strong>License status:</strong>{' '}
        {license ? license.status : 'no_license'}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr)',
          rowGap: '0.5rem',
        }}
      >
        {/* Pipeline execution */}
        <FeatureButtonRow
          label="Run pipeline"
          description="Execute data pipelines."
          featureKey="pipeline_execution"
          allowed={hasPipelineExecution}
          disabledReason={disabledReason('pipeline_execution', hasPipelineExecution)}
          onClick={() => handleDummyClick('Run pipeline')}
        />

        {/* Advanced export */}
        <FeatureButtonRow
          label="Advanced export"
          description="Use advanced export features."
          featureKey="advanced_export"
          allowed={hasAdvancedExport}
          disabledReason={disabledReason('advanced_export', hasAdvancedExport)}
          onClick={() => handleDummyClick('Advanced export')}
        />

        {/* Custom connectors */}
        <FeatureButtonRow
          label="Custom connectors"
          description="Configure and run custom connectors."
          featureKey="custom_connectors"
          allowed={hasCustomConnectors}
          disabledReason={disabledReason('custom_connectors', hasCustomConnectors)}
          onClick={() => handleDummyClick('Custom connectors')}
        />
      </div>

      {license && license.features && (
        <details
          style={{
            marginTop: '0.75rem',
            fontSize: '0.8rem',
          }}
        >
          <summary>Raw features from license</summary>
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
{JSON.stringify(license.features, null, 2)}
          </pre>
        </details>
      )}
    </div>
  )
}

function FeatureButtonRow({
  label,
  description,
  featureKey,
  allowed,
  disabledReason,
  onClick,
}) {
  const disabled = !allowed

  return (
    <div
      style={{
        padding: '0.6rem 0.8rem',
        borderRadius: '0.6rem',
        border: '1px solid #e5e7eb',
        backgroundColor: '#f9fafb',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '0.75rem',
      }}
    >
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
          {description}
        </div>
        <div style={{ fontSize: '0.75rem', marginTop: '0.2rem' }}>
          <strong>Feature key:</strong> <code>{featureKey}</code>
        </div>
        {disabled && disabledReason && (
          <div
            style={{
              fontSize: '0.75rem',
              marginTop: '0.25rem',
              color: '#b91c1c',
            }}
          >
            {disabledReason}
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={disabled ? undefined : onClick}
        disabled={disabled}
        style={{
          whiteSpace: 'nowrap',
          padding: '0.35rem 0.8rem',
          fontSize: '0.8rem',
          borderRadius: '999px',
          border: 'none',
          cursor: disabled ? 'not-allowed' : 'pointer',
          backgroundColor: disabled ? '#e5e7eb' : '#2563eb',
          color: disabled ? '#6b7280' : '#ffffff',
          fontWeight: 500,
        }}
      >
        {disabled ? 'Not available' : 'Use feature'}
      </button>
    </div>
  )
}
