
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import ContactHero from "@/components/contact/ContactHero";
import ContactInfo from "@/components/contact/ContactInfo";
import ContactForm from "@/components/contact/ContactForm";
import ContactFaqSection from "@/components/contact/ContactFaqSection";
import { Helmet } from "react-helmet-async";

const Contact = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Helmet>
        <title>お問い合わせ | ワークメイトAI - AIチャットボットで業務効率化</title>
        <meta name="description" content="ワークメイトAIの業務効率化AIチャットボットについてのお問い合わせページです。導入やトライアルに関するご質問など、お気軽にお問い合わせください。" />
        <meta name="keywords" content="ワークメイトAI, お問い合わせ, AIチャットボット, 業務効率化AI, サポート, 問い合わせフォーム" />
        <meta property="og:title" content="お問い合わせ | ワークメイトAI" />
        <meta property="og:description" content="ワークメイトAIの業務効率化AIチャットボットについてのお問い合わせページです。" />
        <meta property="og:type" content="website" />
        <link rel="canonical" href="https://www.workmate-ai.jp/contact" />
      </Helmet>
      
      <Navbar />
      <main className="flex-grow pt-28">
        {/* Hero Section */}
        <ContactHero />

        {/* Contact Info + Form Section */}
        <section className="py-16">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="max-w-6xl mx-auto">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                {/* Contact Information */}
                <ContactInfo />
                
                {/* Contact Form */}
                <ContactForm />
              </div>
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <ContactFaqSection />
      </main>
      <Footer />
    </div>
  );
};

export default Contact;
