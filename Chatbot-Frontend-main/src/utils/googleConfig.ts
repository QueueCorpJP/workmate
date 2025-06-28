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
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
  'application/vnd.ms-excel', // .xls
  'application/vnd.ms-excel.sheet.macroEnabled.12', // .xlsm
  'application/vnd.ms-excel.sheet.binary.macroEnabled.12', // .xlsb
  'text/plain',
  'text/csv', // .csv
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  'application/msword', // .doc
  'application/vnd.google-apps.document',
  'application/vnd.google-apps.spreadsheet',
  'application/vnd.google-apps.presentation',
  'application/rtf', // Rich Text Format
  'text/html', // HTML files
  'application/json', // JSON files
  'application/xml', // XML files
  'text/xml' // XML files
];