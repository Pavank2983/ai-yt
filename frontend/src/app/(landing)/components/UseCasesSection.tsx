"use client";

import { useEffect } from "react";
import { TrendingUp, Users, Sparkles, Target } from "lucide-react";

interface UseCaseProps {
    icon: React.ReactNode;
    title: string;
    description: string;
    stats: string;
    delay: string;
}

function UseCaseCard({ icon, title, description, stats, delay }: UseCaseProps) {
    return (
        <div
            className="use-case-card glass-card p-6 hover:scale-105 transition-all duration-300 opacity-0"
            style={{ animationDelay: delay }}
        >
            <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/30 flex items-center justify-center flex-shrink-0">
                    {icon}
                </div>

                <div>
                    <h3 className="text-xl font-bold mb-1">{title}</h3>
                    <p className="text-sm text-primary font-semibold">{stats}</p>
                </div>
            </div>

            <p className="text-muted-foreground leading-relaxed">{description}</p>
        </div>
    );
}

export default function UseCasesSection() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("animate-fade-in");
            entry.target.classList.remove("opacity-0");
          }
        });
      },
      {
        threshold: 0.2,
        rootMargin: "0px 0px -10% 0px", // ensures early trigger
      }
    );

    const elements = document.querySelectorAll(
      ".use-case-card, .use-case-header"
    );
    elements.forEach((el) => observer.observe(el));

    return () => elements.forEach((el) => observer.unobserve(el));
  }, []);

  const useCases = [
    {
      icon: <TrendingUp className="w-6 h-6 text-primary" />,
      title: "Content Creators",
      description:
        "Generate daily Shorts to grow your audience, increase engagement, and monetize faster. Perfect for YouTubers building their brand.",
      stats: "10x Output",
    },
    {
      icon: <Users className="w-6 h-6 text-accent" />,
      title: "Marketing Agencies",
      description:
        "Scale content production for multiple clients simultaneously. Deliver professional Shorts without hiring a video team.",
      stats: "50+ Clients",
    },
    {
      icon: (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-4 h-4 text-primary"
        >
          <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
          <path d="M20 3v4" />
          <path d="M22 5h-4" />
          <path d="M4 17v2" />
          <path d="M5 18H3" />
        </svg>
      ),
      title: "Entrepreneurs",
      description:
        "Build your personal brand with consistent, high-quality content. Share insights, tips, and stories without spending hours editing.",
      stats: "Daily Posting",
    },
    {
      icon: <Target className="w-6 h-6 text-accent" />,
      title: "Course Creators",
      description:
        "Turn course content into bite-sized promotional Shorts. Drive traffic to your courses with engaging video snippets.",
      stats: "3x Conversions",
    },
  ];

  return (
    <section className="section-container relative" id="use-cases">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent"></div>

      <div className="relative z-10">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="use-case-header section-title mb-4 opacity-0 transition-opacity">
            Who Uses This <span className="gradient-text">System?</span>
          </h2>

          <p className="use-case-header text-lg text-muted-foreground max-w-2xl mx-auto mb-4 opacity-0 transition-opacity">
            500+ active creators leverage this automation pipeline to scale their content production.
          </p>

          <p className="use-case-header text-sm text-primary font-semibold opacity-0 transition-opacity">
            Join the creator community building with advanced AI tools
          </p>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          {useCases.map((useCase, index) => (
            <UseCaseCard
              key={index}
              {...useCase}
              delay={`${index * 0.1}s`}
            />
          ))}
        </div>

        {/* Stats Section */}
        <div className="mt-20 glass-card p-8 max-w-4xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold gradient-text mb-2">10K+</div>
              <p className="text-sm text-muted-foreground">Videos Created</p>
            </div>
            <div>
              <div className="text-4xl font-bold gradient-text mb-2">500+</div>
              <p className="text-sm text-muted-foreground">Active Creators</p>
            </div>
            <div>
              <div className="text-4xl font-bold gradient-text mb-2">95%</div>
              <p className="text-sm text-muted-foreground">Satisfaction Rate</p>
            </div>
            <div>
              <div className="text-4xl font-bold gradient-text mb-2">24/7</div>
              <p className="text-sm text-muted-foreground">Automation</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

