import { get, post } from './httpClient'

export async function fetchLicenseStatus() {
  return get('/api/license/status/')
}

export async function uploadLicenseDocument(licenseDocument) {
  return post('/api/license/upload/', {
    license: licenseDocument,
  })
}
