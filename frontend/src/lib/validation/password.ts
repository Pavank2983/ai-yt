export function validatePassword(password: string, confirmPassword: string) {
    const rules = {
        hasUpperLower: /[a-z]/.test(password) && /[A-Z]/.test(password),
        hasNumber: /\d/.test(password),
        minLength: password.length >= 8,
        noSpaces: password.trim() === password,
        match: password === confirmPassword,
    };

    const isValid = Object.values(rules).every(Boolean);

    return { isValid, rules };
}
