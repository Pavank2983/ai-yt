import Navbar from "@/app/(routes)/landing/components/Navbar";
import Hero from "@/app/(routes)/landing/components/Hero";
import Features from "@/app/(routes)/landing/components/Features";
import WorkflowSection from "@/app/(routes)/landing/components/WorkflowSection";
import UseCasesSection from "@/app/(routes)/landing/components/UseCasesSection";
import DemoVideoSection from "@/app/(routes)/landing/components/DemoVideoSection";
import SocialFollowSection from "@/app/(routes)/landing/components/SocialFollowSection";
import Footer from "@/app/(routes)/landing/components/Footer";

export default function LandingPage() {
    return (
        <main className="flex min-h-screen flex-col bg-background" style={{ paddingTop: "4rem" }}>
            <Navbar />
            <Hero />
            <Features />
            <WorkflowSection />
            <UseCasesSection />
            <DemoVideoSection />
            <SocialFollowSection />
            <Footer />
        </main>
    );
}
