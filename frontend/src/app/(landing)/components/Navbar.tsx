"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Menu, X } from "lucide-react";

import {
    Dialog,
    DialogContent,
    DialogTitle,
} from "@/components/ui/dialog";

import { VisuallyHidden } from "@radix-ui/react-visually-hidden";

import LoginForm from "@/components/auth/LoginForm";
import RegisterForm from "@/components/auth/RegisterForm";
import UserMenu from "@/components/common/UserMenu"; // NEW
import { useAuth } from "@/context/AuthContext"; // NEW

export default function Navbar() {
    const [isScrolled, setIsScrolled] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    // Modal states
    const [loginOpen, setLoginOpen] = useState(false);
    const [registerOpen, setRegisterOpen] = useState(false);

    // Global auth (NEW)
    const { user, loading } = useAuth();
    
    const isLoggedIn = !!user;

    /* ---------------------------
       HANDLE NAVBAR SCROLL EFFECT
    --------------------------- */
    useEffect(() => {
        const handleScroll = () => setIsScrolled(window.scrollY > 20);
        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    const navLinks = [
        { label: "Features", href: "#features" },
        { label: "How It Works", href: "#workflow" },
        { label: "Demo", href: "#demo" },
        { label: "Follow", href: "#follow" },
    ];

    return (
        <>
            {/* LOGIN MODAL */}
            <Dialog open={loginOpen} onOpenChange={setLoginOpen}>
                <DialogContent className="p-0 max-w-md rounded-xl overflow-hidden">
                    <VisuallyHidden><DialogTitle>Login</DialogTitle></VisuallyHidden>
                    <LoginForm isModal={true} onClose={() => setLoginOpen(false)} />
                </DialogContent>
            </Dialog>

            {/* REGISTER MODAL */}
            <Dialog open={registerOpen} onOpenChange={setRegisterOpen}>
                <DialogContent className="p-0 max-w-md rounded-xl overflow-hidden">
                    <VisuallyHidden><DialogTitle>Register</DialogTitle></VisuallyHidden>
                    <RegisterForm isModal={true} onClose={() => setRegisterOpen(false)} />
                </DialogContent>
            </Dialog>

            {/* NAVBAR */}
            <nav
                className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled
                        ? "bg-background/80 backdrop-blur-xl border-b border-border shadow-lg"
                        : "bg-transparent"
                    }`}
            >
                <div className="section-container py-4">
                    <div className="flex items-center justify-between">

                        {/* Logo */}
                        <div className="flex items-center gap-2">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    width="24"
                                    height="24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    className="w-6 h-6 text-white"
                                >
                                    <path d="M9.9 15.5A2 2 0 0 0 8.5 14l-6.1-1.6a.5.5 0 0 1 0-.9L8.5 10a2 2 0 0 0 1.4-1.4l1.6-6.1a.5.5 0 0 1 .9 0L14 8.5a2 2 0 0 0 1.4 1.4l6.1 1.6a.5.5 0 0 1 0 .9L15.5 14a2 2 0 0 0-1.4 1.4l-1.6 6.1a.5.5 0 0 1-.9 0z" />
                                </svg>
                            </div>
                            <span className="text-xl font-bold gradient-text">AI Shorts</span>
                        </div>

                        {/* Desktop Navigation Links */}
                        <div className="hidden md:flex items-center gap-8">
                            {navLinks.map((link) => (
                                <a
                                    key={link.href}
                                    href={link.href}
                                    className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                                >
                                    {link.label}
                                </a>
                            ))}
                        </div>

                        {/* Desktop Actions */}
                        <div className="hidden md:flex items-center gap-4">
                            {/* Global auth loaded */}
                            {!loading && (
                                <>
                                    {!isLoggedIn ? (
                                        <>
                                            <Button size="sm" className="neon-glow" onClick={() => setLoginOpen(true)}>
                                                Login
                                            </Button>
                                            <Button size="sm" className="neon-glow" onClick={() => setRegisterOpen(true)}>
                                                Register
                                            </Button>
                                        </>
                                    ) : (
                                        <UserMenu home />
                                    )}
                                </>
                            )}
                        </div>

                        {/* Mobile Menu Toggle */}
                        <button
                            className="md:hidden p-2"
                            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                        >
                            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                        </button>
                    </div>

                    {/* Mobile Menu */}
                    {isMobileMenuOpen && (
                        <div className="md:hidden mt-4 pt-4 border-t border-border">
                            <div className="flex flex-col gap-4">

                                {navLinks.map((link) => (
                                    <a
                                        key={link.href}
                                        href={link.href}
                                        className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                                        onClick={() => setIsMobileMenuOpen(false)}
                                    >
                                        {link.label}
                                    </a>
                                ))}

                                <div className="flex flex-col gap-2 pt-4">

                                    {!loading && (
                                        <>
                                            {!isLoggedIn ? (
                                                <>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => {
                                                            setLoginOpen(true);
                                                            setIsMobileMenuOpen(false);
                                                        }}
                                                    >
                                                        Login
                                                    </Button>

                                                    <Button
                                                        size="sm"
                                                        className="neon-glow"
                                                        onClick={() => {
                                                            setRegisterOpen(true);
                                                            setIsMobileMenuOpen(false);
                                                        }}
                                                    >
                                                        Register
                                                    </Button>
                                                </>
                                            ) : (
                                                // Mobile UserMenu
                                                <div className="px-1 py-2">
                                                    <UserMenu home />
                                                </div>
                                            )}
                                        </>
                                    )}

                                </div>

                            </div>
                        </div>
                    )}
                </div>
            </nav>
        </>
    );
}
