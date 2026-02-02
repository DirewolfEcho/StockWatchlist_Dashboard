const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const getHeaders = (email?: string | null) => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (email) headers["X-User-Email"] = email;
    return headers;
};

export const fetchStocks = async (email?: string | null) => {
    const headers: Record<string, string> = {};
    let url = `${API_URL}/stocks`;

    if (email) {
        headers["X-User-Email"] = email;
        url += `?user_email=${encodeURIComponent(email)}`;
    }

    const res = await fetch(url, {
        headers,
        cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch stocks");
    return res.json();
};


export const addStock = async (symbol: string, market: string, email?: string | null) => {
    let url = `${API_URL}/stocks`;
    if (email) {
        url += `?user_email=${encodeURIComponent(email)}`;
    }

    const res = await fetch(url, {
        method: "POST",
        headers: getHeaders(email),
        body: JSON.stringify({ symbol, market }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
};

export const removeStock = async (symbol: string, email?: string | null) => {
    const headers = getHeaders(email);
    let url = `${API_URL}/stocks/${symbol}`;
    if (email) {
        url += `?user_email=${encodeURIComponent(email)}`;
    }

    const res = await fetch(url, {
        method: "DELETE",
        headers: headers
    });
    if (!res.ok) throw new Error(await res.text());
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
