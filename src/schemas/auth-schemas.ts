
import * as z from "zod";

export const signupFormSchema = z.object({
  company: z.string().min(1, {
    message: "会社名を入力してください。",
  }),
  email: z.string().email({
    message: "有効なメールアドレスを入力してください。",
  }),
  password: z.string().min(8, {
    message: "パスワードは8文字以上である必要があります。",
  }),
  confirmPassword: z.string(),
  terms: z.boolean().refine(val => val === true, {
    message: "利用規約とプライバシーポリシーに同意する必要があります。",
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "パスワードが一致しません。",
  path: ["confirmPassword"],
});

export type SignupFormValues = z.infer<typeof signupFormSchema>;
