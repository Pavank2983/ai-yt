/* -----------------------------------------------
   Script API Functions
------------------------------------------------ */
export async function getScript(id: string) {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/scripts/${id}`,
        { credentials: "include" }
    );

    if (!res.ok) {
        throw Object.assign(new Error("Failed to fetch script"), {
            status: res.status,
        });
    }

    return res.json();
}

export async function analyzeScript(id: string) {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/scripts/${id}/analyze`,
        {
            method: "POST",
            credentials: "include",
        }
    );

    if (!res.ok) {
        throw Object.assign(new Error("Analyze failed"), { status: res.status });
    }

    return res.json();
}

/* -----------------------------------------------
   Generate Video (Manual Dispatch)
------------------------------------------------ */
export async function generateVideo(scriptId: string) {
    const res = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/scripts/${scriptId}/generate-video`,
        {
            method: "POST",
            credentials: "include",
        }
    );

    if (!res.ok) {
        throw Object.assign(new Error("Video generation dispatch failed"), {
            status: res.status,
        });
    }

    return res.json();
}
