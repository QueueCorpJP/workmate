import { useMemo } from 'react';

interface User {
  email?: string;
  role?: string;
  is_special_admin?: boolean;
}

interface PermissionFlags {
  is_special_admin: boolean;
  is_admin_user: boolean;
  is_user: boolean;
  can_delete: boolean;
  can_create: boolean;
  can_access_all_data: boolean;
}

/**
 * 権限判定フック
 * バックエンドのget_permission_flags()と同等の権限判定を提供
 */
export const usePermissions = (user: User | null): PermissionFlags => {
  return useMemo(() => {
    if (!user) {
      return {
        is_special_admin: false,
        is_admin_user: false,
        is_user: false,
        can_delete: false,
        can_create: false,
        can_access_all_data: false,
      };
    }

    // 特別管理者の判定
    const is_special_admin = Boolean(
      user.email &&
      ["queue@queuefood.co.jp", "queue@queueu-tech.jp"].includes(user.email)
    );

    // admin_userロールの判定
    const is_admin_user = user.role === "admin_user";

    // userロールの判定
    const is_user = user.role === "user";

    // 削除権限（admin_userまたは特別管理者）
    const can_delete = is_admin_user || is_special_admin;

    // 作成権限（admin_user、user、または特別管理者）
    const can_create = is_admin_user || is_user || is_special_admin;

    // 全データアクセス権限（特別管理者のみ）
    const can_access_all_data = is_special_admin;

    return {
      is_special_admin,
      is_admin_user,
      is_user,
      can_delete,
      can_create,
      can_access_all_data,
    };
  }, [user]);
};

export default usePermissions; 