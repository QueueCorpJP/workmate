
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { useParams } from "react-router-dom";
import { jobPositions } from "@/components/application/JobDetailsFields";

// Combining all schemas
const formSchema = z.object({
  name: z.string().min(1, { message: "名前を入力してください" }),
  email: z.string().email({ message: "正しいメールアドレスを入力してください" }),
  phone: z.string().optional(),
  position: z.string().min(1, { message: "職種を選択してください" }),
  employmentType: z.string().min(1, { message: "雇用形態を選択してください" }),
  coverLetter: z.string().min(10, { message: "自己PRは10文字以上で入力してください" }),
  resume: z.any().optional(),
});

export type ApplicationFormValues = z.infer<typeof formSchema>;

export const useApplicationForm = () => {
  const { id } = useParams<{ id: string }>();
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  
  // Initialize the form with default values
  const form = useForm<ApplicationFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      email: "",
      phone: "",
      position: id || "",
      employmentType: "",
      coverLetter: "",
      resume: undefined,
    },
  });
  
  // Get job title based on ID
  const jobTitle = id && jobPositions[id as keyof typeof jobPositions]
    ? jobPositions[id as keyof typeof jobPositions].title
    : "応募職種未選択";
  
  // Handle form submission
  const onSubmit = async (values: ApplicationFormValues) => {
    setSubmitting(true);
    try {
      let resumeUrl = null;
      
      // Upload resume if one was provided
      if (resumeFile) {
        const fileExt = resumeFile.name.split('.').pop();
        const fileName = `${Math.random().toString(36).substring(2)}.${fileExt}`;
        const filePath = `resumes/${fileName}`;
        
        // Upload file to Supabase storage
        const { error: uploadError, data } = await supabase.storage
          .from('resumes')
          .upload(filePath, resumeFile);
          
        if (uploadError) {
          throw uploadError;
        }
        
        // Get the public URL for the uploaded file
        const { data: { publicUrl } } = supabase.storage
          .from('resumes')
          .getPublicUrl(filePath);
          
        resumeUrl = publicUrl;
      }
      
      // Store application in database
      const { error } = await supabase
        .from('job_applications')
        .insert({
          name: values.name,
          email: values.email,
          phone: values.phone || null,
          position: values.position,
          employment_type: values.employmentType,
          resume_url: resumeUrl,
          cover_letter: values.coverLetter,
        });
      
      if (error) {
        throw error;
      }
      
      // Show success state
      setSuccess(true);
      toast.success("応募が完了しました", {
        description: "内容を確認の上、ご連絡いたします。"
      });
      
      // Reset form after successful submission
      setTimeout(() => {
        form.reset();
        setResumeFile(null);
      }, 1000);
      
    } catch (error: any) {
      console.error("Application submission error:", error);
      toast.error("エラーが発生しました", {
        description: error.message || "応募の送信に失敗しました。お手数ですが、再度お試しください。"
      });
    } finally {
      setSubmitting(false);
    }
  };

  return {
    form,
    jobTitle,
    submitting,
    success,
    resumeFile,
    setResumeFile,
    onSubmit,
  };
};
