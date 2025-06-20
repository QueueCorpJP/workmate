
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminHeader from "@/components/admin/AdminHeader";
import AdminSidebar from "@/components/admin/AdminSidebar";
import { Helmet } from "react-helmet-async";
import { toast } from "sonner";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from "@/components/ui/dialog";
import { UserPlus, Search, Edit, Trash2, Shield, Mail } from "lucide-react";

// モックデータ - 実際の実装ではAPIから取得します
const mockUsers = [
  { id: 1, name: "山田太郎", email: "yamada@example.com", role: "admin", status: "active", lastLogin: "2023-06-15" },
  { id: 2, name: "佐藤花子", email: "sato@example.com", role: "user", status: "active", lastLogin: "2023-06-10" },
  { id: 3, name: "鈴木一郎", email: "suzuki@example.com", role: "user", status: "inactive", lastLogin: "2023-05-22" },
  { id: 4, name: "田中誠", email: "tanaka@example.com", role: "user", status: "active", lastLogin: "2023-06-14" },
  { id: 5, name: "伊藤涼子", email: "ito@example.com", role: "manager", status: "active", lastLogin: "2023-06-13" }
];

const AdminUsers = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");
  const [isAddUserOpen, setIsAddUserOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);

  // 管理者チェック
  React.useEffect(() => {
    const userRole = localStorage.getItem("userRole");
    if (userRole !== "admin") {
      toast.error("管理者権限が必要です");
      navigate("/login");
    }
  }, [navigate]);

  // ユーザー検索
  const filteredUsers = mockUsers.filter(user => 
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // ユーザー編集
  const handleEditUser = (user: any) => {
    setSelectedUser(user);
    toast.info(`${user.name}のプロフィールを編集中`);
    // 実際の実装ではダイアログを開くなどの処理
  };

  // ユーザー削除
  const handleDeleteUser = (user: any) => {
    if (window.confirm(`${user.name}のアカウントを削除してもよろしいですか？`)) {
      toast.success(`${user.name}のアカウントを削除しました`);
      // 実際の実装ではAPIに削除リクエストを送信
    }
  };

  // 権限変更
  const handleRoleChange = (user: any, newRole: string) => {
    toast.success(`${user.name}の権限を${newRole}に変更しました`);
    // 実際の実装ではAPIに更新リクエストを送信
  };

  // メール送信
  const handleSendEmail = (user: any) => {
    toast.info(`${user.email}にメールを送信しました`);
    // 実際の実装ではメール送信モーダルを表示
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      <Helmet>
        <title>ユーザー管理 | Queue株式会社</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      
      <AdminSidebar />
      
      <div className="flex-1 flex flex-col">
        <AdminHeader />
        
        <main className="flex-1 p-6">
          <div className="container mx-auto">
            <div className="flex justify-between items-center mb-6">
              <h1 className="text-2xl font-bold">ユーザー管理</h1>
              <Button onClick={() => setIsAddUserOpen(true)}>
                <UserPlus className="mr-2 h-4 w-4" />
                新規ユーザー追加
              </Button>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <div className="flex items-center mb-4">
                <div className="relative flex-grow">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    placeholder="ユーザー名またはメールで検索..."
                    className="pl-10"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
              
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ユーザー名</TableHead>
                    <TableHead>メールアドレス</TableHead>
                    <TableHead>権限</TableHead>
                    <TableHead>ステータス</TableHead>
                    <TableHead>最終ログイン</TableHead>
                    <TableHead>アクション</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.name}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          user.role === 'admin' 
                            ? 'bg-purple-100 text-purple-800' 
                            : user.role === 'manager' 
                              ? 'bg-blue-100 text-blue-800' 
                              : 'bg-gray-100 text-gray-800'
                        }`}>
                          {user.role === 'admin' ? '管理者' : user.role === 'manager' ? 'マネージャー' : 'ユーザー'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          user.status === 'active' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.status === 'active' ? 'アクティブ' : '停止中'}
                        </span>
                      </TableCell>
                      <TableCell>{user.lastLogin}</TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button variant="ghost" size="icon" onClick={() => handleEditUser(user)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => handleDeleteUser(user)}>
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => handleRoleChange(user, 'admin')}>
                            <Shield className="h-4 w-4 text-purple-500" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => handleSendEmail(user)}>
                            <Mail className="h-4 w-4 text-blue-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        </main>
      </div>
      
      {/* 新規ユーザー追加ダイアログ */}
      <Dialog open={isAddUserOpen} onOpenChange={setIsAddUserOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新規ユーザー追加</DialogTitle>
            <DialogDescription>
              新しいユーザーの情報を入力してください。
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <label htmlFor="name" className="text-right">ユーザー名</label>
              <Input id="name" className="col-span-3" />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <label htmlFor="email" className="text-right">メールアドレス</label>
              <Input id="email" type="email" className="col-span-3" />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <label htmlFor="role" className="text-right">権限</label>
              <select id="role" className="col-span-3 h-10 rounded-md border border-input px-3 py-2">
                <option value="user">一般ユーザー</option>
                <option value="manager">マネージャー</option>
                <option value="admin">管理者</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setIsAddUserOpen(false)}>キャンセル</Button>
            <Button onClick={() => {
              toast.success("新規ユーザーを追加しました");
              setIsAddUserOpen(false);
            }}>追加</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminUsers;
