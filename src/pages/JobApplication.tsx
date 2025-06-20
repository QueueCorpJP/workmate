
import React from "react";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import { useApplicationForm } from "@/hooks/useApplicationForm";
import PersonalInfoFields from "@/components/application/PersonalInfoFields";
import JobDetailsFields from "@/components/application/JobDetailsFields";
import ResumeUpload from "@/components/application/ResumeUpload";
import CoverLetterField from "@/components/application/CoverLetterField";
import SubmissionSuccess from "@/components/application/SubmissionSuccess";
import ApplicationHeader from "@/components/application/ApplicationHeader";
import { ApplicationSidebar } from "@/components/job/ApplicationSidebar";

const JobApplication = () => {
  const {
    form,
    jobTitle,
    submitting,
    success,
    resumeFile,
    setResumeFile,
    onSubmit
  } = useApplicationForm();
  
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        {/* Header */}
        <ApplicationHeader jobTitle={jobTitle} />
        
        {/* Application Form Section */}
        <section className="py-16">
          <div className="container px-4 mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
              <div className="lg:col-span-2">
                {success ? (
                  <SubmissionSuccess />
                ) : (
                  <Card className="border-gray-100 shadow-sm">
                    <CardContent className="p-8">
                      <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                          <div className="space-y-8">
                            {/* Personal Information */}
                            <PersonalInfoFields form={form} />
                            
                            {/* Job Details */}
                            <JobDetailsFields form={form} />
                            
                            {/* Resume Upload */}
                            <ResumeUpload 
                              resumeFile={resumeFile}
                              setResumeFile={setResumeFile}
                            />
                            
                            {/* Cover Letter */}
                            <CoverLetterField form={form} />
                          </div>
                          
                          <div className="pt-4 border-t border-gray-200">
                            <Button 
                              type="submit" 
                              className="w-full bg-primary hover:bg-primary/90"
                              disabled={submitting}
                            >
                              {submitting ? (
                                <>
                                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                  送信中...
                                </>
                              ) : "応募する"}
                            </Button>
                          </div>
                        </form>
                      </Form>
                    </CardContent>
                  </Card>
                )}
              </div>
              
              {/* Sidebar */}
              <div className="lg:col-span-1">
                <ApplicationSidebar />
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default JobApplication;
