"use client";

import { useEffect } from "react";
import { Play } from "lucide-react";

export default function DemoVideoSection() {
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

        const elements = document.querySelectorAll(".demo-fade");
        elements.forEach((el) => observer.observe(el));

        return () => {
            elements.forEach((el) => observer.unobserve(el));
        };
    }, []);

    return (
        <section className="section-container relative" id="demo">
            {/* Background decoration */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/10 rounded-full blur-[120px]"></div>

            <div className="relative z-10">
                {/* Header */}
                <div className="text-center mb-12">
                    <h2 className="demo-fade section-title mb-4">
                        See It <span className="gradient-text">In Action</span>
                    </h2>
                    <p className="demo-fade text-lg text-muted-foreground max-w-2xl mx-auto">
                        Watch a full AI-generated Short created by this automation system.
                    </p>
                </div>

                {/* Video preview */}
                <div className="demo-fade max-w-md mx-auto">
                    <div className="glass-card p-3 neon-glow">
                        <div className="relative aspect-[9/16] rounded-xl overflow-hidden bg-gradient-to-br from-primary/20 to-accent/20">
                            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-accent/10 flex items-center justify-center">
                                <div className="text-center">
                                    {/* Play Icon */}
                                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-primary/30 backdrop-blur-sm border border-primary/40 flex items-center justify-center hover:scale-110 transition-transform cursor-pointer">
                                        <Play className="w-10 h-10 text-primary" />
                                    </div>

                                    <p className="text-sm text-muted-foreground">AI-Generated Demo Short</p>
                                    <p className="text-xs text-primary mt-2">1080x1920 • Automated Pipeline</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Stats Row */}
                    <div className="mt-6 grid grid-cols-3 gap-4 text-center">
                        <div>
                            <div className="text-2xl font-bold gradient-text">30s</div>
                            <p className="text-xs text-muted-foreground">Generation Time</p>
                        </div>
                        <div>
                            <div className="text-2xl font-bold gradient-text">5+</div>
                            <p className="text-xs text-muted-foreground">AI Models Used</p>
                        </div>
                        <div>
                            <div className="text-2xl font-bold gradient-text">100%</div>
                            <p className="text-xs text-muted-foreground">Automated</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
