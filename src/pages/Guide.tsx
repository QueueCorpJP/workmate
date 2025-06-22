import React from 'react';
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { Helmet } from 'react-helmet-async';

const Guide = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Helmet>
        <title>WorkMate AIチャットボット - 完全使い方ガイド</title>
        <meta name="description" content="WorkMate AIチャットボットの完全使い方ガイド。権限体系、機能詳細、管理者・従業員向けの詳細な使用方法を解説。" />
        <meta name="keywords" content="WorkMate AI, チャットボット, 使い方ガイド, 管理者ガイド, 従業員ガイド, AI チャット" />
        <meta property="og:title" content="WorkMate AIチャットボット - 完全使い方ガイド" />
        <meta property="og:description" content="WorkMate AIチャットボットの完全使い方ガイド。権限体系、機能詳細、管理者・従業員向けの詳細な使用方法を解説。" />
        <meta property="og:type" content="website" />
        <link rel="canonical" href="https://workmatechat.com/guide" />
      </Helmet>
      
      <Navbar />
      <main className="flex-grow pt-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          
          {/* ヘッダー */}
          <div className="text-center mb-16">
            <img 
              src="/work_mate.png" 
              alt="WorkMate Logo" 
              className="mx-auto mb-8 h-24 w-auto"
            />
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              WorkMate AIチャットボット
            </h1>
            <h2 className="text-3xl font-semibold text-blue-600 mb-6">
              完全使い方ガイド
            </h2>
            <div className="w-24 h-1 bg-blue-600 mx-auto"></div>
          </div>

          {/* 目次 */}
          <div className="bg-gray-50 rounded-lg p-8 mb-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              📋 目次
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ul className="space-y-2">
                <li><a href="#system-overview" className="text-blue-600 hover:text-blue-800 transition-colors">システム概要</a></li>
                <li><a href="#authority-system" className="text-blue-600 hover:text-blue-800 transition-colors">権限体系と機能一覧</a></li>
                <li><a href="#admin-guide" className="text-blue-600 hover:text-blue-800 transition-colors">管理者向け使い方ガイド</a></li>
                <li><a href="#employee-guide" className="text-blue-600 hover:text-blue-800 transition-colors">従業員向け使い方ガイド</a></li>
              </ul>
              <ul className="space-y-2">
                <li><a href="#feature-details" className="text-blue-600 hover:text-blue-800 transition-colors">機能詳細表</a></li>
                <li><a href="#authority-comparison" className="text-blue-600 hover:text-blue-800 transition-colors">権限比較表</a></li>
                <li><a href="#faq" className="text-blue-600 hover:text-blue-800 transition-colors">よくある質問</a></li>
                <li><a href="#troubleshooting" className="text-blue-600 hover:text-blue-800 transition-colors">トラブルシューティング</a></li>
              </ul>
            </div>
          </div>

          {/* システム概要 */}
          <section id="system-overview" className="mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">システム概要</h2>
            <div className="bg-white rounded-lg shadow-md p-8">
              <p className="text-lg text-gray-700 mb-6">
                <strong>WorkMate AI</strong> は、企業内のドキュメントやナレッジベースを活用したAIチャットボットシステムです。高性能なAIを搭載し、PDF、Excel、動画などの多様なフォーマットのドキュメントを処理・分析して、従業員の質問に的確な回答を提供します。
              </p>
              
              <h3 className="text-xl font-semibold text-gray-900 mb-4">🎯 主な特徴</h3>
              <ul className="space-y-3 text-gray-700">
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  <span><strong>階層的権限システム</strong>: 特別管理者・管理者・一般ユーザー・従業員の4段階権限</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  <span><strong>多様なファイル形式対応</strong>: PDF、Excel、Word、テキスト、動画、URL</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  <span><strong>リアルタイム分析</strong>: AI分析による利用状況の可視化</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  <span><strong>会社別データ分離</strong>: 会社ごとに完全に分離されたデータ管理</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  <span><strong>利用制限機能</strong>: デモ版・本番版による段階的利用</span>
                </li>
              </ul>
            </div>
          </section>

          {/* 権限体系と機能一覧 */}
          <section id="authority-system" className="mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">権限体系と機能一覧</h2>
            
            <div className="bg-white rounded-lg shadow-md p-8 mb-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">🔐 権限レベル</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full table-auto">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">権限レベル</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">対象ユーザー</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">説明</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    <tr>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">特別管理者</td>
                      <td className="px-4 py-3 text-sm text-gray-700">queue@queueu-tech.jp</td>
                      <td className="px-4 py-3 text-sm text-gray-700">システム全体の最高権限</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">admin</td>
                      <td className="px-4 py-3 text-sm text-gray-700">一般管理者</td>
                      <td className="px-4 py-3 text-sm text-gray-700">全社の管理権限</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">admin_user</td>
                      <td className="px-4 py-3 text-sm text-gray-700">会社社長・代表</td>
                      <td className="px-4 py-3 text-sm text-gray-700">会社レベルの管理権限</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">user</td>
                      <td className="px-4 py-3 text-sm text-gray-700">部門管理者・マネージャー</td>
                      <td className="px-4 py-3 text-sm text-gray-700">部門レベルの管理権限</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">employee</td>
                      <td className="px-4 py-3 text-sm text-gray-700">一般社員</td>
                      <td className="px-4 py-3 text-sm text-gray-700">チャット機能のみ利用可能</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">📊 権限別アクセス可能機能</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full table-auto text-sm">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-3 py-2 text-left font-semibold text-gray-900">機能カテゴリ</th>
                      <th className="px-3 py-2 text-center font-semibold text-gray-900">特別管理者</th>
                      <th className="px-3 py-2 text-center font-semibold text-gray-900">admin</th>
                      <th className="px-3 py-2 text-center font-semibold text-gray-900">admin_user</th>
                      <th className="px-3 py-2 text-center font-semibold text-gray-900">user</th>
                      <th className="px-3 py-2 text-center font-semibold text-gray-900">employee</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    <tr>
                      <td className="px-3 py-2 font-medium text-gray-900">チャット機能</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 font-medium text-gray-900">管理画面アクセス</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 font-medium text-gray-900">ユーザー作成</td>
                      <td className="px-3 py-2 text-center text-green-600">admin_userのみ</td>
                      <td className="px-3 py-2 text-center text-green-600">全て</td>
                      <td className="px-3 py-2 text-center text-green-600">user・employee</td>
                      <td className="px-3 py-2 text-center text-green-600">employeeのみ</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 font-medium text-gray-900">ユーザー削除</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">user・employee</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 font-medium text-gray-900">全社員情報アクセス</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">同一会社のみ</td>
                      <td className="px-3 py-2 text-center text-green-600">同一会社のみ</td>
                      <td className="px-3 py-2 text-center text-yellow-600">自分のみ</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 font-medium text-gray-900">リソース管理</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 font-medium text-gray-900">分析機能</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 font-medium text-gray-900">デモ統計</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* 管理者向け使い方ガイド */}
          <section id="admin-guide" className="mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">管理者向け使い方ガイド</h2>
            
            <div className="space-y-8">
              {/* 初回ログインとセットアップ */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">🚀 初回ログインとセットアップ</h3>
                
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">1. ログイン</h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <pre className="text-sm text-gray-700">
{`URL: https://workmatechat.com
デフォルト管理者アカウント:
- メールアドレス: queue@queuefood.co.jp
- パスワード: John.Queue2025`}
                    </pre>
                  </div>
                </div>

                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">2. 会社名設定</h4>
                  <ol className="list-decimal list-inside space-y-2 text-gray-700">
                    <li>ログイン後、右上のプロフィールアイコンをクリック</li>
                    <li>「設定」を選択</li>
                    <li>会社名を入力して保存</li>
                  </ol>
                </div>

                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-3">3. 管理画面アクセス</h4>
                  <p className="text-gray-700">
                    右上メニューから「管理画面」をクリック、または直接 <code className="bg-gray-100 px-2 py-1 rounded text-sm">https://workmatechat.com/admin</code> にアクセス
                  </p>
                </div>
              </div>

              {/* リソース管理 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">📁 リソース管理</h3>
                
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">ドキュメントアップロード</h4>
                  
                  <div className="mb-4">
                    <h5 className="font-medium text-gray-900 mb-2">対応ファイル形式と制限:</h5>
                    <div className="overflow-x-auto">
                      <table className="min-w-full table-auto text-sm">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="px-3 py-2 text-left font-semibold text-gray-900">ファイル形式</th>
                            <th className="px-3 py-2 text-left font-semibold text-gray-900">最大サイズ</th>
                            <th className="px-3 py-2 text-left font-semibold text-gray-900">対応機能</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          <tr>
                            <td className="px-3 py-2 font-medium text-gray-900">PDF</td>
                            <td className="px-3 py-2 text-gray-700">10MB</td>
                            <td className="px-3 py-2 text-gray-700">OCR、複数ページ対応</td>
                          </tr>
                          <tr>
                            <td className="px-3 py-2 font-medium text-gray-900">Excel (.xlsx, .csv)</td>
                            <td className="px-3 py-2 text-gray-700">5MB</td>
                            <td className="px-3 py-2 text-gray-700">複数シート、データ分析</td>
                          </tr>
                          <tr>
                            <td className="px-3 py-2 font-medium text-gray-900">Word (.docx)</td>
                            <td className="px-3 py-2 text-gray-700">5MB</td>
                            <td className="px-3 py-2 text-gray-700">テキスト抽出</td>
                          </tr>
                          <tr>
                            <td className="px-3 py-2 font-medium text-gray-900">テキスト (.txt, .md)</td>
                            <td className="px-3 py-2 text-gray-700">2MB</td>
                            <td className="px-3 py-2 text-gray-700">プレーンテキスト</td>
                          </tr>
                          <tr>
                            <td className="px-3 py-2 font-medium text-gray-900">動画 (.mp4, .avi, .webm)</td>
                            <td className="px-3 py-2 text-gray-700">500MB</td>
                            <td className="px-3 py-2 text-gray-700">音声認識、内容分析</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="mb-4">
                    <h5 className="font-medium text-gray-900 mb-2">アップロード手順:</h5>
                    <ol className="list-decimal list-inside space-y-2 text-gray-700">
                      <li>管理画面の「リソース」タブを選択</li>
                      <li>「ファイルアップロード」セクションでファイルを選択</li>
                      <li>ファイルをドラッグ&ドロップまたは「ファイルを選択」をクリック</li>
                      <li>アップロード完了まで待機</li>
                      <li>必要に応じて「管理者指令」を設定</li>
                    </ol>
                  </div>
                </div>

                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">URL リソース追加</h4>
                  <ol className="list-decimal list-inside space-y-2 text-gray-700">
                    <li>「URLリソース」セクションでURLを入力</li>
                    <li>「追加」ボタンをクリック</li>
                    <li>Webページの内容が自動的に分析・追加される</li>
                  </ol>
                </div>

                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">Google Drive 連携</h4>
                  <ol className="list-decimal list-inside space-y-2 text-gray-700">
                    <li>「Google Drive連携」ボタンをクリック</li>
                    <li>Googleアカウントでの認証を完了</li>
                    <li>必要なファイルを選択してインポート</li>
                  </ol>
                </div>

                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-3">管理者指令の設定</h4>
                  <p className="text-gray-700 mb-2">
                    各リソースに対してAIの回答方針を指定可能
                  </p>
                  <p className="text-gray-600 text-sm mb-2">
                    例: "このドキュメントの内容は機密性が高いため、詳細な回答は避けてください"
                  </p>
                  <p className="text-gray-700">
                    リソース一覧で「指令設定」をクリックして編集
                  </p>
                </div>
              </div>

              {/* ユーザー管理 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">👥 ユーザー管理</h3>
                
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">新規ユーザー作成</h4>
                  
                  <div className="mb-4">
                    <h5 className="font-medium text-gray-900 mb-2">権限別作成可能アカウント:</h5>
                    <ul className="space-y-2 text-gray-700">
                      <li><strong>特別管理者</strong>: admin_userのみ作成可能</li>
                      <li><strong>admin</strong>: 全権限のアカウント作成可能</li> 
                      <li><strong>admin_user</strong>: user・employeeアカウント作成可能</li>
                      <li><strong>user</strong>: employeeアカウントのみ作成可能</li>
                    </ul>
                  </div>

                  <div>
                    <h5 className="font-medium text-gray-900 mb-2">作成手順:</h5>
                    <ol className="list-decimal list-inside space-y-2 text-gray-700">
                      <li>管理画面の「ユーザー管理」タブを選択</li>
                      <li>「新規アカウント作成」をクリック</li>
                      <li>必要情報を入力:
                        <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                          <li>氏名</li>
                          <li>メールアドレス</li>
                          <li>パスワード</li>
                          <li>権限レベル</li>
                          <li>会社名（新規会社の場合）</li>
                        </ul>
                      </li>
                      <li>「アカウント作成」をクリック</li>
                    </ol>
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-3">既存ユーザー管理</h4>
                  <ul className="space-y-2 text-gray-700">
                    <li><strong>利用状況確認</strong>: 各ユーザーの質問回数、最終アクティビティ</li>
                    <li><strong>デモ/本番切り替え</strong>: 利用制限の変更</li>
                    <li><strong>アカウント削除</strong>: 削除権限がある場合のみ実行可能</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* 従業員向け使い方ガイド */}
          <section id="employee-guide" className="mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">従業員向け使い方ガイド</h2>
            
            <div className="space-y-8">
              {/* 基本的な使い方 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">🌟 基本的な使い方</h3>
                
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">1. ログイン方法</h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <pre className="text-sm text-gray-700">
{`URL: https://workmatechat.com
管理者から発行されたアカウント情報でログイン:
- メールアドレス: （管理者から通知）
- パスワード: （管理者から通知）`}
                    </pre>
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-3">2. チャット画面の構成</h4>
                  <ul className="space-y-2 text-gray-700">
                    <li><strong>左パネル</strong>: ドキュメント情報・URL入力</li>
                    <li><strong>右パネル</strong>: AIとのチャット</li>
                    <li><strong>上部メニュー</strong>: プロフィール・設定・利用状況</li>
                  </ul>
                </div>
              </div>

              {/* AIチャット機能 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">💬 AIチャット機能</h3>
                
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">基本的な質問方法</h4>
                  <ol className="list-decimal list-inside space-y-2 text-gray-700">
                    <li>右側のチャット入力欄に質問を入力</li>
                    <li>Enterキーまたは送信ボタンをクリック</li>
                    <li>AIが関連するドキュメントを参照して回答</li>
                    <li>回答の下に情報ソースが表示される</li>
                  </ol>
                </div>

                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">効果的な質問のコツ</h4>
                  
                  <div className="mb-4">
                    <h5 className="font-medium text-green-600 mb-2">✅ 良い質問例:</h5>
                    <ul className="space-y-1 text-gray-700">
                      <li>• "新入社員の研修スケジュールについて教えてください"</li>
                      <li>• "経費精算の手続きはどのようにすればよいですか？"</li>
                      <li>• "〇〇プロジェクトの進捗状況を確認したい"</li>
                      <li>• "この商品の技術仕様について詳しく知りたい"</li>
                    </ul>
                  </div>

                  <div>
                    <h5 className="font-medium text-red-600 mb-2">❌ 避けるべき質問例:</h5>
                    <ul className="space-y-1 text-gray-700">
                      <li>• "これ" "あれ" など曖昧な表現</li>
                      <li>• 複数の全く異なる質問を一度に送信</li>
                      <li>• 個人的な質問や業務に関係のない質問</li>
                    </ul>
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-3">情報ソースの確認</h4>
                  <ul className="space-y-2 text-gray-700">
                    <li>各回答の下に「📄 参照ソース」が表示される</li>
                    <li>クリックすると元のドキュメント名やページが確認できる</li>
                    <li>情報の信頼性を確認する際に活用</li>
                  </ul>
                </div>
              </div>

              {/* 利用状況の確認 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">📈 利用状況の確認</h3>
                
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">利用制限の確認方法</h4>
                  <ol className="list-decimal list-inside space-y-2 text-gray-700">
                    <li>右上のプロフィールアイコンをクリック</li>
                    <li>「利用状況」を選択</li>
                    <li>以下の情報を確認:
                      <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                        <li><strong>今月の質問回数</strong>: 残り回数/制限回数</li>
                        <li><strong>ドキュメントアップロード</strong>: 残り回数/制限回数</li>
                        <li><strong>アカウント種別</strong>: デモ版/本番版</li>
                      </ul>
                    </li>
                  </ol>
                </div>

                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-3">デモ版の制限について</h4>
                  <ul className="space-y-2 text-gray-700">
                    <li><strong>質問回数制限</strong>: 月50回まで（例）</li>
                    <li><strong>ドキュメントアップロード</strong>: 月5回まで（例）</li>
                    <li><strong>制限到達時</strong>: 管理者に本番版移行を依頼</li>
                  </ul>
                </div>
              </div>

              {/* プロフィール設定 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">🛠️ プロフィール設定</h3>
                
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">個人情報の更新</h4>
                  <ol className="list-decimal list-inside space-y-2 text-gray-700">
                    <li>右上のプロフィールアイコンをクリック</li>
                    <li>「設定」を選択</li>
                    <li>以下の情報を更新可能:
                      <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                        <li>表示名</li>
                        <li>パスワード変更</li>
                        <li>通知設定</li>
                      </ul>
                    </li>
                  </ol>
                </div>

                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">パスワード変更</h4>
                  <ol className="list-decimal list-inside space-y-2 text-gray-700">
                    <li>設定画面で「パスワード変更」をクリック</li>
                    <li>現在のパスワードを入力</li>
                    <li>新しいパスワードを入力（2回）</li>
                    <li>「変更」をクリック</li>
                  </ol>
                </div>

                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-3">📱 モバイル利用</h4>
                  <div className="mb-4">
                    <h5 className="font-medium text-gray-900 mb-2">スマートフォン・タブレットでの利用</h5>
                    <ul className="space-y-2 text-gray-700">
                      <li><strong>レスポンシブデザイン</strong>: 自動的に画面サイズに最適化</li>
                      <li><strong>タッチ操作</strong>: タップ・スワイプで直感的な操作</li>
                      <li><strong>音声入力</strong>: 一部ブラウザで音声入力に対応</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-medium text-gray-900 mb-2">推奨ブラウザ</h5>
                    <ul className="space-y-1 text-gray-700">
                      <li><strong>Chrome</strong>: 最新版推奨</li>
                      <li><strong>Safari</strong>: iOS 14以降</li>
                      <li><strong>Firefox</strong>: 最新版推奨</li>
                      <li><strong>Edge</strong>: 最新版推奨</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* 機能詳細表 */}
          <section id="feature-details" className="mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">機能詳細表</h2>
            
            <div className="space-y-8">
              {/* チャット機能詳細 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">📋 チャット機能詳細</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full table-auto">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">機能</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">説明</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">利用可能権限</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">制限事項</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">テキストチャット</td>
                        <td className="px-4 py-3 text-sm text-gray-700">AIとのテキストベース対話</td>
                        <td className="px-4 py-3 text-sm text-gray-700">全ユーザー</td>
                        <td className="px-4 py-3 text-sm text-gray-700">月間質問回数制限（デモ版）</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">ファイル参照チャット</td>
                        <td className="px-4 py-3 text-sm text-gray-700">アップロード済みファイルを参照した回答</td>
                        <td className="px-4 py-3 text-sm text-gray-700">全ユーザー</td>
                        <td className="px-4 py-3 text-sm text-gray-700">会社内ファイルのみ参照</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">URL参照チャット</td>
                        <td className="px-4 py-3 text-sm text-gray-700">指定URLの内容を参照した回答</td>
                        <td className="px-4 py-3 text-sm text-gray-700">全ユーザー</td>
                        <td className="px-4 py-3 text-sm text-gray-700">一部サイトはアクセス制限あり</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">チャット履歴</td>
                        <td className="px-4 py-3 text-sm text-gray-700">過去の質問・回答の保存・検索</td>
                        <td className="px-4 py-3 text-sm text-gray-700">全ユーザー</td>
                        <td className="px-4 py-3 text-sm text-gray-700">個人のチャット履歴のみ</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">情報ソース表示</td>
                        <td className="px-4 py-3 text-sm text-gray-700">回答の根拠となったドキュメント表示</td>
                        <td className="px-4 py-3 text-sm text-gray-700">全ユーザー</td>
                        <td className="px-4 py-3 text-sm text-gray-700">-</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">感情分析</td>
                        <td className="px-4 py-3 text-sm text-gray-700">チャットの感情（ポジティブ/ネガティブ）分析</td>
                        <td className="px-4 py-3 text-sm text-gray-700">管理者のみ確認</td>
                        <td className="px-4 py-3 text-sm text-gray-700">-</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* リソース管理機能詳細 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">🗂️ リソース管理機能詳細</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full table-auto">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">機能</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">説明</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">利用可能権限</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">制限事項</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">ファイルアップロード</td>
                        <td className="px-4 py-3 text-sm text-gray-700">PDF、Excel、Word等のアップロード</td>
                        <td className="px-4 py-3 text-sm text-gray-700">user以上</td>
                        <td className="px-4 py-3 text-sm text-gray-700">ファイルサイズ・形式制限</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">URL追加</td>
                        <td className="px-4 py-3 text-sm text-gray-700">Webページの内容をリソースとして追加</td>
                        <td className="px-4 py-3 text-sm text-gray-700">user以上</td>
                        <td className="px-4 py-3 text-sm text-gray-700">一部サイトは取得不可</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">Google Drive連携</td>
                        <td className="px-4 py-3 text-sm text-gray-700">Google Driveからのファイル取得</td>
                        <td className="px-4 py-3 text-sm text-gray-700">user以上</td>
                        <td className="px-4 py-3 text-sm text-gray-700">認証が必要</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">リソース有効/無効化</td>
                        <td className="px-4 py-3 text-sm text-gray-700">リソースの利用可否切り替え</td>
                        <td className="px-4 py-3 text-sm text-gray-700">user以上</td>
                        <td className="px-4 py-3 text-sm text-gray-700">-</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">リソース削除</td>
                        <td className="px-4 py-3 text-sm text-gray-700">不要なリソースの削除</td>
                        <td className="px-4 py-3 text-sm text-gray-700">admin、admin_user</td>
                        <td className="px-4 py-3 text-sm text-gray-700">削除権限が必要</td>
                      </tr>
                      <tr>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">管理者指令設定</td>
                        <td className="px-4 py-3 text-sm text-gray-700">AIの回答方針をリソース別に指定</td>
                        <td className="px-4 py-3 text-sm text-gray-700">user以上</td>
                        <td className="px-4 py-3 text-sm text-gray-700">-</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </section>

          {/* 権限比較表 */}
          <section id="authority-comparison" className="mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">権限比較表</h2>
            
            <div className="bg-white rounded-lg shadow-md p-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">🔐 詳細権限マトリックス</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full table-auto text-sm">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-3 py-2 text-left font-semibold text-gray-900">操作・機能</th>
                      <th className="px-3 py-2 text-center font-semibold text-gray-900">特別管理者</th>
                      <th className="px-3 py-2 text-center font-semibold text-gray-900">admin</th>
                      <th className="px-3 py-2 text-center font-semibold text-gray-900">admin_user</th>
                      <th className="px-3 py-2 text-center font-semibold text-gray-900">user</th>
                      <th className="px-3 py-2 text-center font-semibold text-gray-900">employee</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    <tr>
                      <td colSpan={6} className="px-3 py-2 font-bold text-gray-900 bg-gray-100">システム管理</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 text-gray-700">デモ統計閲覧</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 text-gray-700">全社データアクセス</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td colSpan={6} className="px-3 py-2 font-bold text-gray-900 bg-gray-100">ユーザー管理</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 text-gray-700">admin_user作成</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 text-gray-700">admin作成</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 text-gray-700">user作成</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 text-gray-700">employee作成</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td colSpan={6} className="px-3 py-2 font-bold text-gray-900 bg-gray-100">リソース管理</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 text-gray-700">アップロード</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 text-gray-700">有効/無効切り替え</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 text-gray-700">削除</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-green-600">✅</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                      <td className="px-3 py-2 text-center text-red-600">❌</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* よくある質問 */}
          <section id="faq" className="mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">よくある質問</h2>
            
            <div className="space-y-6">
              {/* ログイン・認証関連 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">🤔 ログイン・認証関連</h3>
                
                <div className="space-y-6">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Q: パスワードを忘れた場合はどうすればよいですか？</h4>
                    <p className="text-gray-700">A: 管理者にパスワードリセットを依頼してください。現在、セルフサービスでのパスワードリセット機能は提供していません。</p>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Q: ログインできない場合の対処法は？</h4>
                    <div className="text-gray-700">
                      <p className="mb-2">A: 以下を確認してください：</p>
                      <ol className="list-decimal list-inside space-y-1">
                        <li>メールアドレス・パスワードの入力ミス</li>
                        <li>Caps Lockの状態</li>
                        <li>ブラウザのCookieが有効になっているか</li>
                        <li>インターネット接続状況</li>
                      </ol>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Q: アカウントがロックされた場合は？</h4>
                    <p className="text-gray-700">A: 管理者に連絡してアカウントロックの解除を依頼してください。</p>
                  </div>
                </div>
              </div>

              {/* チャット機能関連 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">💬 チャット機能関連</h3>
                
                <div className="space-y-6">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Q: AIが適切な回答をしてくれない場合は？</h4>
                    <div className="text-gray-700">
                      <p className="mb-2">A: 以下を試してください：</p>
                      <ol className="list-decimal list-inside space-y-1">
                        <li>より具体的で詳細な質問に変更</li>
                        <li>質問の文脈や背景を追加</li>
                        <li>キーワードを変えて再質問</li>
                        <li>管理者に関連ドキュメントの追加を依頼</li>
                      </ol>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Q: 情報ソースが表示されない回答があるのはなぜ？</h4>
                    <div className="text-gray-700">
                      <p className="mb-2">A: 以下の場合があります：</p>
                      <ol className="list-decimal list-inside space-y-1">
                        <li>AIの一般知識から回答している</li>
                        <li>複数のソースを総合して回答している</li>
                        <li>該当するドキュメントが見つからない</li>
                      </ol>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Q: チャット履歴は他の人に見られますか？</h4>
                    <p className="text-gray-700">A: 基本的に個人のチャット履歴は本人のみ閲覧可能です。ただし、管理者権限のあるユーザーは分析目的で閲覧する場合があります。</p>
                  </div>
                </div>
              </div>

              {/* ファイル・リソース関連 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">📁 ファイル・リソース関連</h3>
                
                <div className="space-y-6">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Q: アップロードできないファイルがあります</h4>
                    <div className="text-gray-700">
                      <p className="mb-2">A: 以下を確認してください：</p>
                      <ol className="list-decimal list-inside space-y-1">
                        <li>ファイルサイズが制限内か（PDF: 10MB、動画: 500MB等）</li>
                        <li>対応形式か（PDF、Excel、Word、テキスト、動画）</li>
                        <li>ファイルが破損していないか</li>
                        <li>アップロード権限があるか</li>
                      </ol>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Q: アップロードしたファイルが反映されません</h4>
                    <div className="text-gray-700">
                      <p className="mb-2">A: ファイル処理には時間がかかる場合があります：</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>PDF: 1-3分</li>
                        <li>Excel: 1-2分</li>
                        <li>動画: 5-15分</li>
                        <li>処理完了後にページを更新してください</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* トラブルシューティング */}
          <section id="troubleshooting" className="mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">トラブルシューティング</h2>
            
            <div className="space-y-8">
              {/* 緊急時の対応 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">🚨 緊急時の対応</h3>
                
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">システムにアクセスできない場合</h4>
                  <ol className="list-decimal list-inside space-y-2 text-gray-700">
                    <li><strong>ブラウザの再起動</strong>: ブラウザを完全に閉じて再起動</li>
                    <li><strong>キャッシュクリア</strong>: Ctrl+F5（Windows）/ Cmd+R（Mac）</li>
                    <li><strong>別ブラウザで試行</strong>: Chrome、Firefox、Safari等</li>
                    <li><strong>インターネット接続確認</strong>: 他のWebサイトにアクセス可能か確認</li>
                  </ol>
                </div>

                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-3">エラーメッセージの対処</h4>
                  <div className="space-y-4">
                    <div>
                      <h5 className="font-medium text-red-600">403 Forbidden エラー</h5>
                      <p className="text-gray-700">原因: アクセス権限不足</p>
                      <p className="text-gray-700">対処: 管理者に権限確認を依頼</p>
                    </div>
                    <div>
                      <h5 className="font-medium text-red-600">500 Internal Server Error</h5>
                      <p className="text-gray-700">原因: サーバー側の一時的問題</p>
                      <p className="text-gray-700">対処: 数分待ってから再試行、継続する場合は管理者に報告</p>
                    </div>
                    <div>
                      <h5 className="font-medium text-red-600">ファイルアップロードエラー</h5>
                      <p className="text-gray-700">原因: ファイルサイズ・形式制限、ネットワーク問題</p>
                      <p className="text-gray-700">対処: ファイル確認、ネットワーク確認後再試行</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* パフォーマンス改善 */}
              <div className="bg-white rounded-lg shadow-md p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">🔧 パフォーマンス改善</h3>
                
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3">動作が重い場合</h4>
                  <ol className="list-decimal list-inside space-y-2 text-gray-700">
                    <li><strong>ブラウザタブの整理</strong>: 不要なタブを閉じる</li>
                    <li><strong>拡張機能の無効化</strong>: 広告ブロッカー等を一時無効化</li>
                    <li><strong>メモリ不足の解消</strong>: 他のアプリケーションを終了</li>
                    <li><strong>ブラウザの更新</strong>: 最新版に更新</li>
                  </ol>
                </div>

                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-3">チャット応答が遅い場合</h4>
                  <ol className="list-decimal list-inside space-y-2 text-gray-700">
                    <li><strong>質問の簡潔化</strong>: 長すぎる質問を短く分割</li>
                    <li><strong>時間帯の変更</strong>: アクセス集中時間を避ける</li>
                    <li><strong>ドキュメント数の確認</strong>: 参照ドキュメントが多すぎる場合は管理者に相談</li>
                  </ol>
                </div>
              </div>

              {/* サポート連絡先 */}
              <div className="bg-blue-50 rounded-lg p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">📞 サポート連絡先</h3>
                
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-900">緊急時連絡先:</h4>
                    <ul className="text-gray-700">
                      <li>システム管理者: queue@queueu-tech.jp</li>
                      <li>技術サポート: [社内ITヘルプデスク]</li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900">通常サポート:</h4>
                    <ul className="text-gray-700">
                      <li>平日 9:00-18:00</li>
                      <li>回答目安: 2営業日以内</li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900">サポート時の準備情報:</h4>
                    <ol className="list-decimal list-inside text-gray-700">
                      <li>発生日時</li>
                      <li>エラーメッセージ（スクリーンショット推奨）</li>
                      <li>利用ブラウザ・OS情報</li>
                      <li>実行していた操作の詳細</li>
                      <li>ユーザーアカウント情報</li>
                    </ol>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* フッター情報 */}
          <div className="text-center py-8 border-t border-gray-200">
            <p className="text-gray-600 mb-2">
              このガイドは WorkMate AI チャットボットシステム v2.0 に基づいて作成されています。
            </p>
            <p className="text-gray-600 mb-4">
              最終更新: 2025年6月22日
            </p>
            <p className="text-gray-500 text-sm">
              © 2025 Queue Corp. All rights reserved.
            </p>
          </div>

        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Guide;
