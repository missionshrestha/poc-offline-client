import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { fetchLicenseStatus } from '../api/licenseApi'


function normalizeLicenseStatus(raw) {
  if (!raw) {
    return null
  }

  return {
    status: raw.status ?? 'unknown',
    statusMessage: raw.status_message ?? '',
    isValid: Boolean(raw.is_valid),

    licenseId: raw.license_id ?? null,
    customerName: raw.customer_name ?? null,
    editionCode: raw.edition_code ?? null,
    editionName: raw.edition_name ?? null,
    licenseType: raw.license_type ?? null,

    validFrom: raw.valid_from ?? null,
    validUntil: raw.valid_until ?? null,

    features: raw.features || {},
    limits: raw.limits || {},

    warnings: Array.isArray(raw.warnings) ? raw.warnings : [],
    raw,
  }
}

const LicenseContext = createContext(null)

export function LicenseProvider({ children }) {
  const [license, setLicense] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function loadStatus() {
    setLoading(true)
    setError(null)
    try {
      const raw = await fetchLicenseStatus()
      const normalized = normalizeLicenseStatus(raw)
      setLicense(normalized)
    } catch (err) {
      console.error('Failed to fetch license status', err)
      setError(err)
      setLicense(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStatus()
  }, [])

  function canUse(featureKey) {
    if (!license || !license.isValid) {
      return false
    }

    if (!featureKey) {
      return true
    }

    const features = license.features || {}
    const feature = features[featureKey]

    if (feature === undefined) {
      return false
    }

    if (typeof feature === 'boolean') {
      return feature
    }

    if (typeof feature === 'object' && feature !== null) {
      if ('enabled' in feature) {
        return Boolean(feature.enabled)
      }
      return true
    }

    return false
  }

  const value = useMemo(
    () => ({
      license,
      loading,
      error,
      // helpers
      canUse,
      refreshLicenseStatus: loadStatus,
    }),
    [license, loading, error],
  )

  return (
    <LicenseContext.Provider value={value}>
      {children}
    </LicenseContext.Provider>
  )
}

export function useLicense() {
  const ctx = useContext(LicenseContext)
  if (!ctx) {
    throw new Error('useLicense must be used inside a <LicenseProvider>')
  }
  return ctx
}
