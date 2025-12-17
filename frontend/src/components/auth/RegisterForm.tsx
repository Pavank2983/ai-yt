"use client";

import { useState } from "react";
import { registerUser } from "@/lib/api/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import AppLogo from "@/components/common/AppLogo";

/* ------------------------ PASSWORD VALIDATION HELPERS ------------------------ */

function getPasswordStrength(password: string) {
    let score = 0;

    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (password.length >= 8) score++;
    if (!password.startsWith(" ") && !password.endsWith(" ")) score++;

    if (score <= 1) return { label: "Weak", color: "red", dots: 1 };
    if (score === 2) return { label: "Medium", color: "yellow", dots: 2 };
    return { label: "Strong", color: "green", dots: 3 };
}

const RuleRow = ({ ok, text }: { ok: boolean; text: string }) => (
    <div className={`flex items-center gap-2 text-sm ${ok ? "text-green-500" : "text-red-500"}`}>
        {ok ? "✓" : "✗"} {text}
    </div>
);

/* -------------------------------------------------------------------------- */

export default function RegisterForm({ isModal = false }: any) {
    const [loading, setLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState("");

    const [form, setForm] = useState({
        name: "",
        email: "",
        password: "",
        confirm: "",
    });

    const [showPassword, setShowPassword] = useState(false);
    const [showPassword2, setShowPassword2] = useState(false);

    const handleChange = (k: string, v: string) => {
        setForm({ ...form, [k]: v });
    };

    /* --------------------------- Email Validation --------------------------- */
    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email);

    /* ----------------------- Real-time Password Rules ------------------------ */
    const rules = {
        hasUpperLower: /[a-z]/.test(form.password) && /[A-Z]/.test(form.password),
        hasNumber: /\d/.test(form.password),
        minLength: form.password.length >= 8,
        noSpaces: !form.password.startsWith(" ") && !form.password.endsWith(" "),
        match: form.password === form.confirm && form.confirm.length > 0,
    };

    const strength = getPasswordStrength(form.password);

    /* ---------------------- ENABLE / DISABLE SUBMIT BUTTON ------------------- */
    const formValid =
        form.name.trim().length > 0 &&
        emailValid &&
        rules.hasUpperLower &&
        rules.hasNumber &&
        rules.minLength &&
        rules.noSpaces &&
        rules.match;

    /* --------------------------- SUBMIT HANDLER ------------------------------ */

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErrorMsg("");

        if (!formValid) {
            setErrorMsg("Please fix all errors before submitting.");
            return;
        }

        setLoading(true);

        try {
            const result = await registerUser(form.name, form.email, form.password);
            console.log("Registration success:", result);

            window.location.href = "/login";
        } catch (err: any) {
            setErrorMsg(err.message);
        } finally {
            setLoading(false);
        }
    };

    /* ----------------------------- UI RENDER -------------------------------- */

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
                        <AppLogo />
                    </div>
                    <h2 className="text-2xl font-semibold mb-2">Create Your Account</h2>
                    <p className="text-muted-foreground">Join the AI Shorts community</p>
                </div>

                {/* Error message */}
                {errorMsg && (
                    <div className="mb-4 text-red-500 text-center text-sm">{errorMsg}</div>
                )}

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Name */}
                    <div className="space-y-2">
                        <Label>Full Name</Label>
                        <Input
                            value={form.name}
                            onChange={(e) => handleChange("name", e.target.value)}
                            placeholder="John Carter"
                            className="bg-background/50 border-border"
                            required
                        />
                    </div>

                    {/* Email */}
                    <div className="space-y-2">
                        <Label>Email Address</Label>
                        <Input
                            type="email"
                            value={form.email}
                            onChange={(e) => handleChange("email", e.target.value)}
                            placeholder="you@example.com"
                            className={`bg-background/50 border ${form.email.length === 0
                                    ? "border-border"
                                    : emailValid
                                        ? ""
                                        : "border-red-500"
                                }`}
                            required
                        />
                        {form.email.length > 0 && !emailValid && (
                            <p className="text-red-500 text-sm">Enter a valid email address</p>
                        )}
                    </div>

                    {/* Password */}
                    <div className="space-y-2">
                        <Label>Password</Label>
                        <div className="relative">
                            <Input
                                type={showPassword ? "text" : "password"}
                                value={form.password}
                                onChange={(e) => handleChange("password", e.target.value)}
                                placeholder="••••••••"
                                className="bg-background/50 border pr-10"
                                required
                            />
                            <button
                                type="button"
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                                onClick={() => setShowPassword(!showPassword)}
                            >
                                {showPassword ? <EyeOff /> : <Eye />}
                            </button>
                        </div>

                        {/* Strength bars */}
                        {form.password && (
                            <div className="flex items-center gap-2 mt-1">
                                {[1, 2, 3].map((i) => (
                                    <div
                                        key={i}
                                        className={`h-2 w-8 rounded-full transition-all ${strength.dots >= i
                                                ? `bg-${strength.color}-500`
                                                : "bg-border"
                                            }`}
                                    />
                                ))}
                                <span className={`text-xs ml-2 text-${strength.color}-400`}>
                                    {strength.label}
                                </span>
                            </div>
                        )}

                        {/* Rule List */}
                        {form.password.length > 0 && (
                            <div className="mt-3 space-y-1 p-3 border border-border rounded-lg bg-background/60 fade-in-up">
                                <RuleRow
                                    ok={rules.hasUpperLower}
                                    text="Must contain both lowercase & uppercase letters"
                                />
                                <RuleRow ok={rules.hasNumber} text="Must contain a number" />
                                <RuleRow ok={rules.minLength} text="Must be at least 8 characters long" />
                                <RuleRow ok={rules.noSpaces} text="Must not have leading or trailing spaces" />
                            </div>
                        )}
                    </div>

                    {/* Confirm Password */}
                    <div className="space-y-2">
                        <Label>Confirm Password</Label>
                        <div className="relative">
                            <Input
                                type={showPassword2 ? "text" : "password"}
                                value={form.confirm}
                                onChange={(e) => handleChange("confirm", e.target.value)}
                                placeholder="••••••••"
                                className="bg-background/50 border pr-10"
                                required
                            />
                            <button
                                type="button"
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                                onClick={() => setShowPassword2(!showPassword2)}
                            >
                                {showPassword2 ? <EyeOff /> : <Eye />}
                            </button>
                        </div>

                        {form.confirm.length > 0 && !rules.match && (
                            <p className="text-red-500 text-sm">Passwords do not match</p>
                        )}
                        {rules.match && form.confirm.length > 0 && (
                            <p className="text-green-500 text-sm">Passwords match ✓</p>
                        )}
                    </div>

                    {/* Submit */}
                    <Button
                        type="submit"
                        className={`w-full h-12 transition-all ${!formValid ? "opacity-50 cursor-not-allowed" : ""
                            }`}
                        disabled={!formValid || loading}
                    >
                        {loading ? "Creating account..." : "Create Account"}
                    </Button>
                </form>

                {/* Login Link */}
                {!isModal && (
                    <div className="mt-6 text-center">
                        <p className="text-muted-foreground mb-2">Already have an account?</p>
                        <Link href="/login">
                            <Button variant="outline" className="w-full h-12">
                                Sign In
                            </Button>
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
}
