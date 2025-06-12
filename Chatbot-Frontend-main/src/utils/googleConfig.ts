export const GOOGLE_CONFIG = {
  clientId: import.meta.env.VITE_GOOGLE_DRIVE_CLIENT_ID,
  apiKey: import.meta.env.VITE_GOOGLE_DRIVE_API_KEY,
  redirectUri: import.meta.env.VITE_GOOGLE_REDIRECT_URI,
  scope: 'https://www.googleapis.com/auth/drive.readonly',
  discoveryDocs: ['https://www.googleapis.com/discovery/v1/apis/drive/v3/rest']
};

export const GOOGLE_DRIVE_SCOPES = [
  'https://www.googleapis.com/auth/drive.readonly'
];

export const SUPPORTED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'text/plain',
  'application/vnd.google-apps.document',
  'application/vnd.google-apps.spreadsheet'
]; 