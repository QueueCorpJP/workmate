
-- Create a storage bucket for resumes
INSERT INTO storage.buckets (id, name)
VALUES ('resumes', 'resumes')
ON CONFLICT (id) DO NOTHING;

-- Set up proper policies for the resumes bucket
-- Allow any user to upload resumes (since we want to allow non-authenticated applicants)
INSERT INTO storage.policies (name, bucket_id, definition, operation)
VALUES 
('Public upload access', 'resumes', '(true)', 'INSERT'),
('Admin select access', 'resumes', '(auth.uid() IN (SELECT id FROM auth.users WHERE email IN (''queue@queuefood.co.jp'', ''taichi.tanigusan@gmail.com'')))
', 'SELECT');
