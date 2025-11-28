import { Sparkles, Twitter, Youtube, Mail } from "lucide-react";

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
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                                {/* <Sparkles className="w-6 h-6 text-white" /> */}
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-sparkles w-6 h-6 text-white" data-lov-id="src/components/AINavbar.tsx:36:14" data-lov-name="Sparkles" data-component-path="src/components/AINavbar.tsx" data-component-line="36" data-component-file="AINavbar.tsx" data-component-name="Sparkles" data-component-content="%7B%22className%22%3A%22w-6%20h-6%20text-white%22%7D"><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"></path><path d="M20 3v4"></path><path d="M22 5h-4"></path><path d="M4 17v2"></path><path d="M5 18H3"></path></svg>
                            </div>
                            <span className="text-xl font-bold gradient-text">AI Shorts</span>
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
