"use client";

import { useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles, Play } from "lucide-react";

export default function Hero() {
    const videoRef = useRef<HTMLDivElement>(null);

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

        const elements = document.querySelectorAll(".fade-in-element");
        elements.forEach((el) => observer.observe(el));

        return () => {
            elements.forEach((el) => observer.unobserve(el));
        };
    }, []);

    return (
        <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
            {/* Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/10"></div>

            {/* Animated Orbs */}
            <div className="absolute top-20 left-10 w-72 h-72 bg-primary/30 rounded-full blur-[100px] animate-pulse-slow"></div>
            <div
                className="absolute bottom-20 right-10 w-96 h-96 bg-accent/20 rounded-full blur-[120px] animate-pulse-slow"
                style={{ animationDelay: "1s" }}
            ></div>

            <div className="section-container relative z-10">
                <div className="max-w-6xl mx-auto text-center">
                    {/* Badge */}
                    <div className="fade-in-element inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
                        {/* <Sparkles className="w-4 h-4 text-primary" /> */}
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 text-primary" data-lov-id="src/components/AIHero.tsx:41:12" data-lov-name="Sparkles" data-component-path="src/components/AIHero.tsx" data-component-line="41" data-component-file="AIHero.tsx" data-component-name="Sparkles" data-component-content="%7B%22className%22%3A%22w-4%20h-4%20text-primary%22%7D"><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"></path><path d="M20 3v4"></path><path d="M22 5h-4"></path><path d="M4 17v2"></path><path d="M5 18H3"></path></svg>
                        <span className="text-sm font-medium text-primary">
                            Built by a Creator, for Creators
                        </span>
                    </div>

                    {/* Tech Badge */}
                    <div className="fade-in-element flex flex-wrap justify-center gap-2 mb-8 text-xs">
                        {["OpenAI", "Sora", "KLING", "Runway", "ElevenLabs"].map((tech) => (
                            <span
                                key={tech}
                                className="px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent"
                            >
                                {tech}
                            </span>
                        ))}
                    </div>

                    {/* Headline */}
                    <h1 className="fade-in-element section-title text-5xl md:text-6xl lg:text-7xl mb-6 leading-tight">
                        AI-Powered YouTube Shorts
                        <br />
                        <span className="gradient-text">Automation System</span>
                    </h1>

                    {/* Subtext */}
                    <p className="fade-in-element text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto mb-12 leading-relaxed">
                        Multi-provider pipeline for script-to-video automation. Scene-by-scene
                        generation, intelligent merging, and vertical formatting—all automated.
                    </p>

                    {/* CTA Buttons */}
                    <div className="fade-in-element flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
                        <Button size="lg" className="text-base px-8 py-6 neon-glow group">
                            View My Work
                            <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </Button>
                        <Button
                            size="lg"
                            variant="outline"
                            className="text-base px-8 py-6 border-primary/30 hover:bg-primary/10 group"
                        >
                            <Play className="mr-2 w-5 h-5 group-hover:scale-110 transition-transform" />
                            See Demo
                        </Button>
                    </div>

                    {/* Demo Preview */}
                    <div ref={videoRef} className="fade-in-element relative max-w-4xl mx-auto">
                        <div className="glass-card p-2 neon-glow">
                            <div className="relative aspect-video rounded-xl overflow-hidden bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-accent/5"></div>
                                <div className="relative z-10 text-center">
                                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-primary/20 backdrop-blur-sm border border-primary/30 flex items-center justify-center">
                                        <Play className="w-10 h-10 text-primary" />
                                    </div>
                                    <p className="text-muted-foreground">Demo Video Preview</p>
                                </div>
                            </div>
                        </div>

                        {/* Floating Elements */}
                        <div className="absolute -top-6 -right-6 w-32 h-32 rounded-2xl bg-primary/10 backdrop-blur-sm border border-primary/20 rotate-12 hidden lg:block"></div>
                        <div className="absolute -bottom-6 -left-6 w-24 h-24 rounded-full bg-accent/10 backdrop-blur-sm border border-accent/20 hidden lg:block"></div>
                    </div>
                </div>
            </div>
        </section>
    );
}
