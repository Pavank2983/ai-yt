"use client";

import { useEffect } from "react";
import { FileText, Mic, Video, Layers, Upload, Zap } from "lucide-react";

interface FeatureCardProps {
    icon: React.ReactNode;
    title: string;
    description: string;
    gradient: string;
}

function FeatureCard({ icon, title, description, gradient }: FeatureCardProps) {
    return (
        <div className="group relative glass-card p-6 hover:scale-105 transition-all duration-300">
            <div
                className={`absolute inset-0 ${gradient} opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity duration-300`}
            ></div>

            <div className="relative z-10">
                <div className="w-14 h-14 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    {icon}
                </div>

                <h3 className="text-xl font-bold mb-2">{title}</h3>
                <p className="text-muted-foreground leading-relaxed">{description}</p>
            </div>
        </div>
    );
}

export default function Features() {
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("animate-fade-in");
                    }
                });
            },
            { threshold: 0.1 }
        );

        const elements = document.querySelectorAll(".feature-fade");
        elements.forEach((el) => observer.observe(el));

        return () => {
            elements.forEach((el) => observer.unobserve(el));
        };
    }, []);

    const features = [
        {
            icon: <FileText className="w-7 h-7 text-primary" />,
            title: "AI Script Writing",
            description:
                "Generate engaging, viral-ready scripts with advanced AI that understands your niche and audience.",
            gradient: "bg-gradient-to-br from-primary/20 to-primary/5",
        },
        {
            icon: <Mic className="w-7 h-7 text-accent" />,
            title: "AI Voiceover",
            description:
                "Choose from OpenAI, ElevenLabs, or Google voices. Natural, expressive narration in seconds.",
            gradient: "bg-gradient-to-br from-accent/20 to-accent/5",
        },
        {
            icon: <Video className="w-7 h-7 text-primary" />,
            title: "AI Video Generation",
            description:
                "Create stunning visuals with Sora, KLING, Runway, or MiniMax. Scene-by-scene perfection.",
            gradient: "bg-gradient-to-br from-primary/20 to-primary/5",
        },
        {
            icon: <Layers className="w-7 h-7 text-accent" />,
            title: "Smart Scene Merging",
            description:
                "Automatically combine scenes into cohesive videos with perfect transitions and timing.",
            gradient: "bg-gradient-to-br from-accent/20 to-accent/5",
        },
        {
            icon: <Zap className="w-7 h-7 text-primary" />,
            title: "Auto Formatting",
            description:
                "Perfectly optimized 1080x1920 vertical videos for YouTube Shorts, TikTok, and Reels.",
            gradient: "bg-gradient-to-br from-primary/20 to-primary/5",
        },
        {
            icon: <Upload className="w-7 h-7 text-accent" />,
            title: "Upload Workflow",
            description:
                "Schedule and auto-upload directly to YouTube. Full content calendar management (coming soon).",
            gradient: "bg-gradient-to-br from-accent/20 to-accent/5",
        },
    ];

    return (
        <section className="section-container" id="features">
            <div className="text-center mb-16">
                <h2 className="feature-fade section-title mb-4">
                    Advanced Multi-Provider <span className="gradient-text">Pipeline</span>
                </h2>

                <p className="feature-fade text-lg text-muted-foreground max-w-2xl mx-auto mb-6">
                    Enterprise-grade automation system powering 10,000+ videos daily with 99.9% uptime.
                </p>

                {/* Credibility Badges */}
                <div className="feature-fade flex flex-wrap justify-center gap-4 text-sm">
                    <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20">
                        <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                        <span className="text-primary font-semibold">10K+ Videos Generated</span>
                    </div>

                    <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-accent/10 border border-accent/20">
                        <div className="w-2 h-2 rounded-full bg-accent animate-pulse"></div>
                        <span className="text-accent font-semibold">24/7 Automated Pipeline</span>
                    </div>

                    <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20">
                        <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                        <span className="text-primary font-semibold">99.9% System Reliability</span>
                    </div>
                </div>
            </div>

            {/* Feature Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {features.map((feature, index) => (
                    <div
                        key={index}
                        className="feature-fade"
                        style={{ animationDelay: `${index * 0.1}s` }}
                    >
                        <FeatureCard {...feature} />
                    </div>
                ))}
            </div>
        </section>
    );
}
