"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Youtube, Twitter, Instagram, TrendingUp, Users, Eye } from "lucide-react";

export default function SocialFollowSection() {
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

        const elements = document.querySelectorAll(".social-fade");
        elements.forEach((el) => observer.observe(el));

        return () => elements.forEach((el) => observer.unobserve(el));
    }, []);

    const socialStats = [
        { icon: <Users className="w-5 h-5" />, label: "Followers", value: "50K+" },
        { icon: <Eye className="w-5 h-5" />, label: "Monthly Views", value: "2M+" },
        { icon: <TrendingUp className="w-5 h-5" />, label: "Videos Created", value: "500+" },
    ];

    return (
        <section className="section-container relative overflow-hidden" id="follow">
            {/* Animated Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-accent/10"></div>
            <div className="absolute top-20 left-20 w-64 h-64 bg-primary/20 rounded-full blur-[100px] animate-pulse-slow"></div>
            <div
                className="absolute bottom-20 right-20 w-64 h-64 bg-accent/20 rounded-full blur-[100px] animate-pulse-slow"
                style={{ animationDelay: "1s" }}
            ></div>

            <div className="relative z-10">
                <div className="glass-card max-w-4xl mx-auto p-8 md:p-12">
                    {/* Header */}
                    <div className="text-center mb-10">
                        <h2 className="social-fade section-title mb-4">
                            Join My <span className="gradient-text">Creator Journey</span>
                        </h2>

                        <p className="social-fade text-lg text-muted-foreground max-w-2xl mx-auto mb-8">
                            Follow along as I build and showcase advanced AI automation tools.
                            Get insights, behind-the-scenes content, and learn how to leverage AI for content creation.
                        </p>

                        {/* Social Stats */}
                        <div className="social-fade grid grid-cols-3 gap-6 max-w-xl mx-auto mb-10">
                            {socialStats.map((stat, index) => (
                                <div key={index} className="text-center">
                                    <div className="w-12 h-12 mx-auto mb-2 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                                        {stat.icon}
                                    </div>

                                    <div className="text-2xl font-bold gradient-text mb-1">{stat.value}</div>
                                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Social Buttons */}
                    <div className="social-fade flex flex-col sm:flex-row gap-4 justify-center items-center">
                        {/* YouTube */}
                        <Button
                            size="lg"
                            className="w-full sm:w-auto bg-[#FF0000] hover:bg-[#CC0000] text-white border-none px-8 group"
                        >
                            <Youtube className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
                            Follow on YouTube
                        </Button>

                        {/* Instagram */}
                        <Button
                            size="lg"
                            variant="outline"
                            className="w-full sm:w-auto border-[#E1306C] text-[#E1306C] hover:bg-[#E1306C]/10 px-8 group"
                        >
                            <Instagram className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
                            Follow on Instagram
                        </Button>

                        {/* Twitter / X */}
                        <Button
                            size="lg"
                            variant="outline"
                            className="w-full sm:w-auto border-primary/50 hover:bg-primary/10 px-8 group"
                        >
                            <Twitter className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
                            Follow on X
                        </Button>
                    </div>

                    {/* Footer Text */}
                    <p className="social-fade text-center text-sm text-muted-foreground mt-8">
                        <span className="text-primary font-semibold">500+ creators</span> already following my AI automation journey
                    </p>
                </div>
            </div>
        </section>
    );
}
