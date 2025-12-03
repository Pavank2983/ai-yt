"use client";

import { useState, useEffect } from "react";
import { loginUser } from "@/lib/api/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, Sparkles } from "lucide-react";
import Link from "next/link";

export default function LoginForm({ isModal = false }: any) {
    const [loading, setLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState("");

    const [showPassword, setShowPassword] = useState(false);

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    // ⭐ AUTO-HIDE ERROR MESSAGE (3 seconds)
    useEffect(() => {
        if (!errorMsg) return;

        const timer = setTimeout(() => {
            setErrorMsg("");
        }, 1500);

        return () => clearTimeout(timer);
    }, [errorMsg]);

    /* ---------------------- VALIDATION RULES ---------------------- */

    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    const passwordValid = password.length >= 8; // minimum requirement

    const formValid = emailValid && passwordValid;

    /* ---------------------- SUBMIT HANDLER ------------------------ */

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErrorMsg("");

        if (!formValid) {
            setErrorMsg("Please fill in valid credentials.");
            return;
        }

        setLoading(true);

        const friendlyMessages: Record<string, string> = {
            "Email not found": "No account exists with this email.",
            "Incorrect password": "Your password is incorrect.",
            "Please verify your email to continue": "Check your inbox to verify your account.",
        };

        try {
            const data = await loginUser(email.trim(), password);
            console.log("Login Success:", data);

            window.location.href = "/dashboard";
        } catch (err: any) {
            const msg = friendlyMessages[err.message] || "Login failed. Try again.";
            setErrorMsg(msg);
        } finally {
            setLoading(false);
        }
    };

    /* ------------------------------ UI ----------------------------- */

    return (
        <div
            className={
                isModal
                    ? "w-full flex justify-center"
                    : "min-h-screen flex items-center justify-center px-4 relative overflow-hidden bg-background"
            }
        >
            {!isModal && (
                <>
                    <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-background to-accent/10 animate-pulse-slow" />
                    <div className="absolute top-20 left-20 w-72 h-72 bg-primary/20 rounded-full blur-3xl animate-pulse-slow" />
                    <div
                        className="absolute bottom-20 right-20 w-96 h-96 bg-accent/20 rounded-full blur-3xl animate-pulse-slow"
                        style={{ animationDelay: "2s" }}
                    />
                </>
            )}

            <div
                className={`${isModal
                        ? "modal-animate"
                        : "glass-card fadeIn shadow-[0_0_30px_rgba(139,92,246,0.25)]"
                    } bg-background/80 backdrop-blur-xl p-8 rounded-2xl w-full max-w-md relative`}
            >
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-2 mb-4">
                        <Sparkles className="w-8 h-8 text-primary" />
                        <h1 className="text-3xl font-display font-bold gradient-text">
                            AI Shorts
                        </h1>
                    </div>
                    <h2 className="text-2xl font-semibold mb-2">Welcome Back</h2>
                    <p className="text-muted-foreground">
                        Sign in to continue to your dashboard
                    </p>
                </div>

                {/* FORM */}
                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Email */}
                    <div className="space-y-2">
                        <Label>Email Address</Label>

                        <Input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
                            className={`bg-background/50 border ${email.length === 0
                                    ? "border-border"
                                    : emailValid
                                        ? ""
                                        : "border-red-500"
                                }`}
                            required
                        />

                        {/* Email Error */}
                        {email.length > 0 && !emailValid && (
                            <p className="text-red-500 text-sm">Enter a valid email.</p>
                        )}
                    </div>

                    {/* Password */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <Label>Password</Label>

                            {!isModal && (
                                <Link
                                    href="/forgot-password"
                                    className="text-sm text-primary hover:text-primary/80"
                                >
                                    Forgot?
                                </Link>
                            )}
                        </div>

                        <div className="relative">
                            <Input
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className={`bg-background/50 border pr-10 ${password.length === 0
                                        ? "border-border"
                                        : passwordValid
                                            ? ""
                                            : "border-red-500"
                                    }`}
                                required
                            />

                            <button
                                type="button"
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                onClick={() => setShowPassword(!showPassword)}
                            >
                                {showPassword ? <EyeOff /> : <Eye />}
                            </button>
                        </div>

                        {!passwordValid && password.length > 0 && (
                            <p className="text-red-500 text-sm">
                                Password must be at least 8 characters.
                            </p>
                        )}
                    </div>

                    {/* Error Message */}
                    {errorMsg && (
                        <div className="mb-4 text-red-500 text-center text-sm">
                            {errorMsg}
                        </div>
                    )}

                    {/* Submit Button */}
                    <Button
                        type="submit"
                        className={`w-full h-12 transition-all ${!formValid ? "opacity-50 cursor-not-allowed" : ""
                            }`}
                        disabled={!formValid || loading}
                    >
                        {loading ? "Signing in..." : "Sign In"}
                    </Button>
                </form>

                {!isModal && (
                    <>
                        <div className="my-8 border-t border-border text-center pt-4 text-muted-foreground">
                            New to AI Shorts?
                        </div>

                        <Link href="/register">
                            <Button variant="outline" className="w-full h-12">
                                Create Account
                            </Button>
                        </Link>

                        <div className="mt-6 text-center">
                            <Link
                                href="/"
                                className="text-sm text-muted-foreground hover:text-primary"
                            >
                                ← Back to Home
                            </Link>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
