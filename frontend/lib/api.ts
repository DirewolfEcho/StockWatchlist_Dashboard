const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const getHeaders = (email?: string | null) => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (email) headers["X-User-Email"] = email;
    return headers;
};

export const fetchStocks = async (email?: string | null) => {
    const headers: Record<string, string> = {};
    if (email) headers["X-User-Email"] = email;

    const res = await fetch(`${API_URL}/stocks`, { headers });
    if (!res.ok) throw new Error("Failed to fetch stocks");
    return res.json();
};


export const addStock = async (symbol: string, market: string, email?: string | null) => {
    const res = await fetch(`${API_URL}/stocks`, {
        method: "POST",
        headers: getHeaders(email),
        body: JSON.stringify({ symbol, market }),
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to add stock");
    }
    return res.json();
};

export const removeStock = async (symbol: string, email?: string | null) => {
    // Delete usually doesn't need content-type, but needs User Email
    const headers: Record<string, string> = {};
    if (email) headers["X-User-Email"] = email;

    const res = await fetch(`${API_URL}/stocks/${symbol}`, {
        method: "DELETE",
        headers: headers
    });
    if (!res.ok) throw new Error("Failed to remove stock");
    return res.json();
};

export const fetchReports = async (dateFilter: string = "today") => {
    // Reports are currently global
    const res = await fetch(`${API_URL}/reports?date_filter=${dateFilter}`);
    if (!res.ok) throw new Error("Failed to fetch reports");
    return res.json();
};

export const setTimer = async (time: string, email?: string | null) => {
    // Timer is global in this MVP, but we could make it user specific later. 
    // For now, let's just pass auth header anyway.
    const res = await fetch(`${API_URL}/settings/timer`, {
        method: "POST",
        headers: getHeaders(email),
        body: JSON.stringify({ time }),
    });
    if (!res.ok) throw new Error("Failed to set timer");
    return res.json();
};

export const triggerAnalysis = async () => {
    const res = await fetch(`${API_URL}/debug/trigger-analysis`, {
        method: "POST",
    });
    if (!res.ok) throw new Error("Failed to trigger analysis");
    return res.json();
};
