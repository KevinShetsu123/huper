/**
 * Vercel Serverless Function - API Proxy
 *
 * This function acts as a proxy between the frontend and the backend,
 * forwarding requests to the backend URL specified in environment variables.
 *
 * Benefits:
 * - Hides the backend URL (Ngrok) from the client
 * - Handles CORS issues
 * - Bypasses Ngrok browser warning screen
 */

module.exports = async (req, res) => {
    // Get backend URL from environment variable
    const BACKEND_URL = process.env.BACKEND_URL;

    if (!BACKEND_URL) {
        return res.status(500).json({
            error: "Backend URL not configured",
            detail: "BACKEND_URL environment variable is not set",
        });
    }

    // Extract the path from the request URL
    // The path will be everything after /api/v1
    const path = req.url.replace(/^\/api\/v1/, "") || "/";

    // Construct the full backend URL (add /api/v1 back for backend routing)
    const backendURL = `${BACKEND_URL}/api/v1${path}`;

    try {
        // Prepare headers
        const headers = {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true", // Bypass Ngrok warning screen
            ...req.headers,
        };

        // Remove host header to avoid conflicts
        delete headers.host;
        delete headers.connection;

        // Prepare fetch options
        const fetchOptions = {
            method: req.method,
            headers: headers,
        };

        // Add body for POST, PUT, PATCH requests
        if (["POST", "PUT", "PATCH"].includes(req.method) && req.body) {
            fetchOptions.body =
                typeof req.body === "string" ?
                    req.body
                :   JSON.stringify(req.body);
        }

        // Forward the request to the backend
        const response = await fetch(backendURL, fetchOptions);

        // Get response data
        const contentType = response.headers.get("content-type");
        let data;

        if (contentType && contentType.includes("application/json")) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        // Forward the response back to the client
        res.status(response.status).json(data);
    } catch (error) {
        console.error("Proxy error:", error);
        res.status(500).json({
            error: "Proxy error",
            detail: error.message,
        });
    }
};
