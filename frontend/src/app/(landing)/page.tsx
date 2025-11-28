import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Features from "./components/Features";
import WorkflowSection from "./components/WorkflowSection";
import UseCasesSection from "./components/UseCasesSection";
import DemoVideoSection from "./components/DemoVideoSection";
import SocialFollowSection from "./components/SocialFollowSection";
import Footer from "./components/Footer";

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
