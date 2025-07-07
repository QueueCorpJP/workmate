// 通知の既読状態をローカルストレージで管理するユーティリティ

export interface Notification {
  id: string;
  title: string;
  content: string;
  notification_type: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

// ローカルストレージのキー
const NOTIFICATION_READ_KEY = 'workmate_read_notifications';

/**
 * 既読通知IDの配列を取得
 */
export const getReadNotificationIds = (): string[] => {
  try {
    const readIds = localStorage.getItem(NOTIFICATION_READ_KEY);
    return readIds ? JSON.parse(readIds) : [];
  } catch (error) {
    console.error('既読通知IDの取得に失敗:', error);
    return [];
  }
};

/**
 * 通知を既読にマーク
 */
export const markNotificationAsRead = (notificationId: string): void => {
  try {
    const readIds = getReadNotificationIds();
    if (!readIds.includes(notificationId)) {
      readIds.push(notificationId);
      localStorage.setItem(NOTIFICATION_READ_KEY, JSON.stringify(readIds));
    }
  } catch (error) {
    console.error('通知の既読マークに失敗:', error);
  }
};

/**
 * 複数の通知を既読にマーク
 */
export const markMultipleNotificationsAsRead = (notificationIds: string[]): void => {
  try {
    const readIds = getReadNotificationIds();
    const updatedReadIds = [...new Set([...readIds, ...notificationIds])];
    localStorage.setItem(NOTIFICATION_READ_KEY, JSON.stringify(updatedReadIds));
  } catch (error) {
    console.error('複数通知の既読マークに失敗:', error);
  }
};

/**
 * 通知が既読かどうかを確認
 */
export const isNotificationRead = (notificationId: string): boolean => {
  const readIds = getReadNotificationIds();
  return readIds.includes(notificationId);
};

/**
 * 未読通知数を計算
 */
export const getUnreadNotificationCount = (notifications: Notification[]): number => {
  const readIds = getReadNotificationIds();
  return notifications.filter(notification => !readIds.includes(notification.id)).length;
};

/**
 * 未読通知のみをフィルタリング
 */
export const getUnreadNotifications = (notifications: Notification[]): Notification[] => {
  const readIds = getReadNotificationIds();
  return notifications.filter(notification => !readIds.includes(notification.id));
};

/**
 * 既読通知のみをフィルタリング
 */
export const getReadNotifications = (notifications: Notification[]): Notification[] => {
  const readIds = getReadNotificationIds();
  return notifications.filter(notification => readIds.includes(notification.id));
};

/**
 * 全ての既読状態をクリア（デバッグ用）
 */
export const clearAllReadNotifications = (): void => {
  try {
    localStorage.removeItem(NOTIFICATION_READ_KEY);
  } catch (error) {
    console.error('既読状態のクリアに失敗:', error);
  }
};

/**
 * 古い既読状態をクリーンアップ（存在しない通知IDを削除）
 */
export const cleanupReadNotifications = (existingNotificationIds: string[]): void => {
  try {
    const readIds = getReadNotificationIds();
    const validReadIds = readIds.filter(id => existingNotificationIds.includes(id));
    localStorage.setItem(NOTIFICATION_READ_KEY, JSON.stringify(validReadIds));
  } catch (error) {
    console.error('既読状態のクリーンアップに失敗:', error);
  }
}; 