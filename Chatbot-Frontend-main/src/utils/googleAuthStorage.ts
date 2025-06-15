interface GoogleAuthData {
  accessToken: string;
  expiresAt: number;
  tokenType: string;
  scope: string;
}

const STORAGE_KEY = 'google_drive_auth';
const COOKIE_NAME = 'google_drive_token';

export class GoogleAuthStorage {
  static setAuthData(authData: {
    access_token: string;
    expires_in: number;
    token_type?: string;
    scope?: string;
  }): void {
    const expiresAt = Date.now() + (authData.expires_in * 1000);
    
    const data: GoogleAuthData = {
      accessToken: authData.access_token,
      expiresAt,
      tokenType: authData.token_type || 'Bearer',
      scope: authData.scope || 'https://www.googleapis.com/auth/drive.readonly'
    };

    // ローカルストレージに保存
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    
    // クッキーにも保存（HTTPOnlyではないが、アクセストークンの永続化用）
    const cookieValue = encodeURIComponent(JSON.stringify(data));
    const expiresDate = new Date(expiresAt);
    document.cookie = `${COOKIE_NAME}=${cookieValue}; expires=${expiresDate.toUTCString()}; path=/; SameSite=Lax`;
  }

  static getAuthData(): GoogleAuthData | null {
    try {
      // まずローカルストレージから取得を試みる
      const storageData = localStorage.getItem(STORAGE_KEY);
      if (storageData) {
        const data = JSON.parse(storageData) as GoogleAuthData;
        if (this.isTokenValid(data)) {
          return data;
        }
      }

      // ローカルストレージに無い場合はクッキーから取得
      const cookieData = this.getCookieValue(COOKIE_NAME);
      if (cookieData) {
        const data = JSON.parse(decodeURIComponent(cookieData)) as GoogleAuthData;
        if (this.isTokenValid(data)) {
          // ローカルストレージにも保存
          localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
          return data;
        }
      }
    } catch (error) {
      console.error('認証データの取得に失敗しました:', error);
    }
    
    return null;
  }

  static getAccessToken(): string | null {
    const authData = this.getAuthData();
    return authData?.accessToken || null;
  }

  static isAuthenticated(): boolean {
    return this.getAccessToken() !== null;
  }

  static clearAuthData(): void {
    localStorage.removeItem(STORAGE_KEY);
    document.cookie = `${COOKIE_NAME}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
  }

  static getTokenExpiryTime(): number | null {
    const authData = this.getAuthData();
    return authData?.expiresAt || null;
  }

  static getTimeUntilExpiry(): number {
    const expiryTime = this.getTokenExpiryTime();
    if (!expiryTime) return 0;
    return Math.max(0, expiryTime - Date.now());
  }

  static willExpireSoon(thresholdMinutes: number = 5): boolean {
    const timeUntilExpiry = this.getTimeUntilExpiry();
    return timeUntilExpiry < (thresholdMinutes * 60 * 1000);
  }

  private static isTokenValid(data: GoogleAuthData): boolean {
    return !!(data && data.accessToken && data.expiresAt > Date.now());
  }

  private static getCookieValue(name: string): string | null {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [cookieName, cookieValue] = cookie.trim().split('=');
      if (cookieName === name) {
        return cookieValue;
      }
    }
    return null;
  }

  // デバッグ用メソッド
  static getAuthStatus(): {
    isAuthenticated: boolean;
    expiresAt: number | null;
    timeUntilExpiry: number;
    willExpireSoon: boolean;
  } {
    return {
      isAuthenticated: this.isAuthenticated(),
      expiresAt: this.getTokenExpiryTime(),
      timeUntilExpiry: this.getTimeUntilExpiry(),
      willExpireSoon: this.willExpireSoon(5)
    };
  }
}