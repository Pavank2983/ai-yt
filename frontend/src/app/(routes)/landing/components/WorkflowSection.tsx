"use client";

import React from "react";
import { useEffect } from "react";
import { ArrowRight } from "lucide-react";

interface StepProps {
    number: string;
    title: string;
    description: string;
    delay: string;
}

function WorkflowStep({ number, title, description, delay }: StepProps) {
    return (
        <div
            className="workflow-step flex items-start gap-4"
            style={{ animationDelay: delay }}
        >
            <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br logo-icon-bg  from-primary  to-accent flex items-center justify-center font-bold text-lg neon-glow">
                {number}
            </div>

            <div className="flex-1">
                <h3 className="text-xl font-bold mb-2">{title}</h3>
                <p className="text-muted-foreground">{description}</p>
            </div>
        </div>
    );
}

export default function WorkflowSection() {
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) =>
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("animate-fade-in");
                    }
                }),
            { threshold: 0.1 }
        );

        const elements = document.querySelectorAll(".workflow-step");
        elements.forEach((el) => observer.observe(el));

        return () => elements.forEach((el) => observer.unobserve(el));
    }, []);

    const steps = [
        {
            number: "1",
            title: "Script Generation",
            description:
                "AI analyzes your topic and creates an engaging, viral-optimized script in seconds.",
        },
        {
            number: "2",
            title: "Voice Synthesis",
            description:
                "Choose your preferred AI voice provider and generate natural-sounding narration.",
        },
        {
            number: "3",
            title: "Scene Creation",
            description:
                "AI generates stunning visuals for each scene using your selected video model.",
        },
        {
            number: "4",
            title: "Smart Merging",
            description:
                "Our pipeline combines scenes with perfect transitions and synchronizes audio.",
        },
        {
            number: "5",
            title: "Final Video",
            description:
                "Get a perfectly formatted 1080x1920 Short, ready for upload to any platform.",
        },
    ];

    return (
        <section className="section-container relative" id="workflow">
            {/* Background Decorations */}
            <div className="absolute top-1/2 left-0 w-64 h-64 bg-primary/10 rounded-full blur-[100px]"></div>
            <div className="absolute top-1/2 right-0 w-64 h-64 bg-accent/10 rounded-full blur-[100px]"></div>

            <div className="relative z-10">
                {/* Header */}
                <div className="text-center mb-16">
                    <h2 className="section-title mb-4">
                        How It <span className="gradient-text">Works</span>
                    </h2>

                    <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                        From script to final video in five automated steps. No editing skills required.
                    </p>
                </div>

                {/* Steps */}
                <div className="max-w-3xl mx-auto">
                    <div className="space-y-8">
                        {steps.map((step, index) => (
                            <React.Fragment key={index}>
                                <WorkflowStep
                                    number={step.number}
                                    title={step.title}
                                    description={step.description}
                                    delay={`${index * 0.15}s`}
                                />

                                {index < steps.length - 1 && (
                                    <div className="flex justify-center">
                                    <ArrowRight className="w-6 h-6 text-primary/50 rotate-90" />
                                    </div>
                                )}
                            </React.Fragment>
                        ))}
                    </div>
                </div>

                {/* Visual Flow */}
                <div className="mt-16 glass-card p-8 max-w-4xl mx-auto">
                    <div className="flex items-center justify-between gap-4 overflow-x-auto">
                        {/* Icons Flow */}
                        <div className="text-center min-w-[100px]">
                            <div className="w-16 h-16 mx-auto rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center mb-2">
                                📝
                            </div>
                            <p className="text-sm text-muted-foreground">Script</p>
                        </div>

                        <ArrowRight className="w-6 h-6 text-primary/50 flex-shrink-0" />

                        <div className="text-center min-w-[100px]">
                            <div className="w-16 h-16 mx-auto rounded-full bg-accent/20 border-2 border-accent flex items-center justify-center mb-2">
                                🎙️
                            </div>
                            <p className="text-sm text-muted-foreground">Voice</p>
                        </div>

                        <ArrowRight className="w-6 h-6 text-primary/50 flex-shrink-0" />

                        <div className="text-center min-w-[100px]">
                            <div className="w-16 h-16 mx-auto rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center mb-2">
                                🎬
                            </div>
                            <p className="text-sm text-muted-foreground">Scenes</p>
                        </div>

                        <ArrowRight className="w-6 h-6 text-primary/50 flex-shrink-0" />

                        <div className="text-center min-w-[100px]">
                            <div className="w-16 h-16 mx-auto rounded-full bg-accent/20 border-2 border-accent flex items-center justify-center mb-2">
                                🔗
                            </div>
                            <p className="text-sm text-muted-foreground">Merge</p>
                        </div>

                        <ArrowRight className="w-6 h-6 text-primary/50 flex-shrink-0" />

                        <div className="text-center min-w-[100px]">
                            <div className="w-16 h-16 mx-auto rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center mb-2">
                                ✨
                            </div>
                            <p className="text-sm text-muted-foreground">Video</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
