
import React from "react";
import { FormProvider } from "react-hook-form";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Helmet } from "react-helmet-async";
import AdminSidebar from "@/components/admin/AdminSidebar";
import ArticleFormHeader from "@/components/admin/articles/ArticleFormHeader";
import ArticleBasicInfoFields from "@/components/admin/articles/ArticleBasicInfoFields";
import ArticleCategoryField from "@/components/admin/articles/ArticleCategoryField";
import ArticlePublishField from "@/components/admin/articles/ArticlePublishField";
import ArticleContentFields from "@/components/admin/articles/ArticleContentFields";
import ArticleFormActions from "@/components/admin/articles/ArticleFormActions";
import ArticleFormSkeleton from "@/components/admin/articles/ArticleFormSkeleton";
import { useArticleForm } from "@/hooks/articles/useArticleForm";
import { FileText, Calendar, Tag } from "lucide-react";

const ArticleForm = () => {
  const { form, isEditing, loading, initialLoading, onSubmit, generateSlug } = useArticleForm();

  if (initialLoading) {
    return (
      <div className="flex min-h-screen bg-gray-100">
        <AdminSidebar />
        <ArticleFormSkeleton />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-100">
      <Helmet>
        <title>{isEditing ? "記事を編集" : "記事を作成"} | ワークメイトAI 管理画面</title>
        <meta name="description" content="ワークメイトAIのヘルプセンター記事を作成・編集するための管理画面です。" />
      </Helmet>
      
      <AdminSidebar />
      
      <div className="flex-1 overflow-auto">
        <div className="max-w-5xl mx-auto p-6 md:p-8">
          <ArticleFormHeader isEditing={isEditing} />
          
          <FormProvider {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid grid-cols-1 gap-6">
                {/* Basic Information Card */}
                <Card className="overflow-hidden border-none shadow-md transition-all hover:shadow-lg">
                  <CardHeader className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
                    <div className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      <CardTitle>基本情報</CardTitle>
                    </div>
                    <CardDescription className="text-indigo-100">
                      記事のタイトルとURLスラッグを設定してください
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <ArticleBasicInfoFields generateSlug={generateSlug} />
                  </CardContent>
                </Card>
                
                {/* Category and Publishing Card */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card className="overflow-hidden border-none shadow-md transition-all hover:shadow-lg">
                    <CardHeader className="bg-gradient-to-r from-emerald-500 to-teal-600 text-white">
                      <div className="flex items-center gap-2">
                        <Tag className="h-5 w-5" />
                        <CardTitle>カテゴリ</CardTitle>
                      </div>
                      <CardDescription className="text-emerald-100">
                        記事のカテゴリを選択してください
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-6">
                      <ArticleCategoryField />
                    </CardContent>
                  </Card>
                  
                  <Card className="overflow-hidden border-none shadow-md transition-all hover:shadow-lg">
                    <CardHeader className="bg-gradient-to-r from-blue-500 to-cyan-600 text-white">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-5 w-5" />
                        <CardTitle>公開設定</CardTitle>
                      </div>
                      <CardDescription className="text-blue-100">
                        記事の公開状態を設定してください
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-6">
                      <ArticlePublishField />
                    </CardContent>
                  </Card>
                </div>
                
                {/* Content Card */}
                <Card className="overflow-hidden border-none shadow-md transition-all hover:shadow-lg">
                  <CardHeader className="bg-gradient-to-r from-amber-500 to-orange-600 text-white">
                    <div className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      <CardTitle>記事内容</CardTitle>
                    </div>
                    <CardDescription className="text-amber-100">
                      記事の抜粋と本文を入力してください
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <ArticleContentFields />
                  </CardContent>
                </Card>
              </div>
              
              <div className="sticky bottom-0 bg-white shadow-md rounded-lg p-4 border-t border-gray-200 z-10">
                <ArticleFormActions 
                  isEditing={isEditing} 
                  loading={loading} 
                />
              </div>
            </form>
          </FormProvider>
        </div>
      </div>
    </div>
  );
};

export default ArticleForm;
