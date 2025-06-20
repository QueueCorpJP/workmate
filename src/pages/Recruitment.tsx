
import React from "react";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import HeroSection from "@/components/recruitment/HeroSection";
import CompanyCulture from "@/components/recruitment/CompanyCulture";
import EmploymentTypes from "@/components/recruitment/EmploymentTypes";
import BenefitsSection from "@/components/recruitment/BenefitsSection";
import OpenPositions from "@/components/recruitment/OpenPositions";
import ContractFaq from "@/components/recruitment/ContractFaq";
import CtaSection from "@/components/recruitment/CtaSection";

const Recruitment = () => {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <HeroSection />
        <CompanyCulture />
        <EmploymentTypes />
        <BenefitsSection />
        <OpenPositions />
        <ContractFaq />
        <CtaSection />
      </main>
      <Footer />
    </div>
  );
};

export default Recruitment;
