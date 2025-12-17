import { Sparkles, Twitter, Youtube, Mail } from "lucide-react";
import AppLogo from "@/components/common/AppLogo";

export default function Footer() {
    const footerLinks = {
        Project: ["Features", "Demo", "Video List"],
        Social: ["YouTube", "Instagram", "Twitter/X"],
        Creator: ["About Me", "Contact"],
    };

    return (
        <footer className="relative border-t border-border bg-background/50 backdrop-blur-xl">
            {/* Background decoration */}
            <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none"></div>

            <div className="section-container relative z-10">
                {/* Main Footer */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-8 py-12 border-b border-border">
                    {/* Brand */}
                    <div className="col-span-1 md:col-span-2">
                        <div className="flex items-center gap-2 mb-4">
                            <AppLogo svgClassName="lucide lucide-sparkles w-6 h-6 text-white"/>
                        </div>

                        <p className="text-sm text-muted-foreground mb-4 max-w-xs">
                            Advanced AI automation system for YouTube Shorts. Built by a creator, showcasing the
                            power of multi-provider AI pipelines.
                        </p>

                        <p className="text-xs text-primary font-semibold mb-4">
                            Follow my journey building AI tools
                        </p>

                        <div className="flex gap-3">
                            <a
                                href="#"
                                className="w-10 h-10 rounded-lg bg-primary/10 hover:bg-primary/20 border border-primary/20 flex items-center justify-center transition-all hover:scale-110"
                            >
                                <Youtube className="w-5 h-5 text-primary" />
                            </a>
                            <a
                                href="#"
                                className="w-10 h-10 rounded-lg bg-primary/10 hover:bg-primary/20 border border-primary/20 flex items-center justify-center transition-all hover:scale-110"
                            >
                                <Twitter className="w-5 h-5 text-primary" />
                            </a>
                            <a
                                href="#"
                                className="w-10 h-10 rounded-lg bg-primary/10 hover:bg-primary/20 border border-primary/20 flex items-center justify-center transition-all hover:scale-110"
                            >
                                <Mail className="w-5 h-5 text-primary" />
                            </a>
                        </div>
                    </div>

                    {/* Link Sections */}
                    {Object.entries(footerLinks).map(([category, links]) => (
                        <div key={category}>
                            <h3 className="font-semibold mb-3 text-sm">{category}</h3>
                            <ul className="space-y-2">
                                {links.map((link) => (
                                    <li key={link}>
                                        <a
                                            href="#"
                                            className="text-sm text-muted-foreground hover:text-primary transition-colors"
                                        >
                                            {link}
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>

                {/* Bottom Bar */}
                <div className="py-6 flex flex-col md:flex-row justify-between items-center gap-4">
                    <p className="text-sm text-muted-foreground">
                        © 2025 AI Shorts Automation. Built with passion.
                    </p>

                    <div className="flex items-center gap-6">
                        <a href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                            Contact
                        </a>
                        <a href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors">
                            Privacy
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    );
}
