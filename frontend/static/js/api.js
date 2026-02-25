/**
 * Hyper Data Lab - API Client
 * Full production version with environment auto-detection
 */

// ===== CONFIGURATION =====
const MOCK_MODE = false; // Set to true for UI-only testing

// Auto-detect environment and set API base URL
let API_BASE_URL;
if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    // Local development - call backend directly
    API_BASE_URL = "http://localhost:8888/api/v1";
    console.log("🔧 Environment: Local Development");
} else {
    // Production (Vercel) - use proxy route
    API_BASE_URL = "/api/v1";
    console.log("🚀 Environment: Production (Vercel)");
}

// Request configuration
const REQUEST_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// ===== API CLIENT =====
class APIClient {
    constructor() {
        this.requestsInProgress = new Map();
    }

    /**
     * Utility: Sleep/delay function
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Utility: Fetch with timeout
     */
    async fetchWithTimeout(url, options = {}, timeout = REQUEST_TIMEOUT) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - server took too long to respond');
            }
            throw error;
        }
    }

    /**
     * Main request method with retry logic and error handling
     */
    async request(endpoint, options = {}, retries = MAX_RETRIES) {
        if (MOCK_MODE) {
            console.log("🚫 MOCK MODE - API disabled:", endpoint);
            return { success: true, data: null, mock: true };
        }

        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: {
                "Content-Type": "application/json",
                "ngrok-skip-browser-warning": "true", // For ngrok tunnels
                ...options.headers,
            },
            ...options,
        };

        console.log(`📡 API Request: ${options.method || 'GET'} ${endpoint}`);

        let lastError;
        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                if (attempt > 0) {
                    console.log(`🔄 Retry attempt ${attempt}/${retries} for ${endpoint}`);
                    await this.sleep(RETRY_DELAY * attempt); // Exponential backoff
                }

                const response = await this.fetchWithTimeout(url, config);

                // Check if response is ok
                if (!response.ok) {
                    const errorData = await this.parseErrorResponse(response);
                    const errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
                    
                    // Don't retry on client errors (4xx)
                    if (response.status >= 400 && response.status < 500) {
                        console.error(`❌ Client error (${response.status}):`, errorData);
                        return { 
                            success: false, 
                            error: errorMessage,
                            errorData: errorData,
                            status: response.status 
                        };
                    }
                    
                    throw new Error(errorMessage);
                }

                // Parse successful response
                const data = await response.json();
                console.log(`✅ API Success: ${endpoint}`);
                return { success: true, data, status: response.status };

            } catch (error) {
                lastError = error;
                console.error(`⚠️ API Error (attempt ${attempt + 1}):`, error.message);
                
                // Don't retry on certain errors
                if (error.message.includes('Failed to fetch') || 
                    error.message.includes('Network request failed')) {
                    // Network errors - worth retrying
                    if (attempt === retries) break;
                    continue;
                }
                
                // For other errors, don't retry
                break;
            }
        }

        // All retries failed
        console.error(`❌ API Failed after ${retries + 1} attempts: ${endpoint}`);
        return { 
            success: false, 
            error: lastError?.message || 'Request failed after multiple attempts',
            retries: retries 
        };
    }

    /**
     * Parse error response - handles both JSON and text responses
     */
    async parseErrorResponse(response) {
        const contentType = response.headers.get('content-type');
        try {
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                const text = await response.text();
                return { detail: text || response.statusText };
            }
        } catch {
            return { detail: response.statusText };
        }
    }

    /**
     * Parse error response - handles both JSON and text responses
     */
    async parseErrorResponse(response) {
        const contentType = response.headers.get('content-type');
        try {
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                const text = await response.text();
                return { detail: text || response.statusText };
            }
        } catch {
            return { detail: response.statusText };
        }
    }

    // ===== SCRAPER ENDPOINTS =====

    /**
     * Scrape financial data for a single stock symbol
     * @param {string} symbol - Stock symbol (e.g., "VNM", "HPG")
     * @param {boolean} headless - Run browser in headless mode
     * @returns {Promise} Response with scraped data
     */
    async scrapeSingle(symbol, headless = true) {
        return this.request("/scraper/scrape", {
            method: "POST",
            body: JSON.stringify({ symbol, headless }),
        });
    }

    /**
     * Scrape financial data for multiple stock symbols
     * @param {string[]} symbols - Array of stock symbols
     * @param {boolean} headless - Run browser in headless mode
     * @returns {Promise} Response with scraped data
     */
    async scrapeBulk(symbols, headless = true) {
        return this.request("/scraper/scrape-bulk", {
            method: "POST",
            body: JSON.stringify({ symbols, headless }),
        });
    }

    // ===== FINANCIAL DATA ENDPOINTS =====

    /**
     * Get financial reports with optional filters
     * @param {Object} params - Query parameters
     * @param {string} params.symbol - Filter by stock symbol
     * @param {string} params.report_type - Filter by report type (annual/quarterly)
     * @param {number} params.report_year - Filter by year
     * @param {number} params.limit - Limit number of results
     * @param {number} params.offset - Offset for pagination
     * @returns {Promise} Response with reports list
     */
    async getReports(params = {}) {
        const queryParams = new URLSearchParams();

        if (params.symbol) queryParams.append("symbol", params.symbol);
        if (params.report_type) queryParams.append("report_type", params.report_type);
        if (params.report_year) queryParams.append("report_year", params.report_year);
        if (params.limit) queryParams.append("limit", params.limit);
        if (params.offset) queryParams.append("offset", params.offset);

        const queryString = queryParams.toString();
        const endpoint = `/financial/reports${queryString ? "?" + queryString : ""}`;

        return this.request(endpoint);
    }

    /**
     * Get a specific financial report by ID
     * @param {number} id - Report ID
     * @returns {Promise} Response with report details
     */
    async getReportById(id) {
        return this.request(`/financial/reports/${id}`);
    }

    /**
     * Get all reports for a specific stock symbol
     * @param {string} symbol - Stock symbol
     * @returns {Promise} Response with reports list
     */
    async getReportsBySymbol(symbol) {
        return this.request(`/financial/reports/symbol/${symbol}`);
    }

    /**
     * Delete a specific financial report
     * @param {number} id - Report ID
     * @returns {Promise} Response confirming deletion
     */
    async deleteReport(id) {
        return this.request(`/financial/reports/${id}`, {
            method: "DELETE",
        });
    }

    /**
     * Delete all reports for a specific stock symbol
     * @param {string} symbol - Stock symbol
     * @returns {Promise} Response confirming deletion
     */
    async deleteReportsBySymbol(symbol) {
        return this.request(`/financial/reports/symbol/${symbol}`, {
            method: "DELETE",
        });
    }

    /**
     * Get database statistics
     * @returns {Promise} Response with stats (total reports, symbols, etc.)
     */
    async getStats() {
        return this.request("/financial/stats");
    }

    /**
     * Get balance sheet items for a specific report
     * @param {number} reportId - Report ID
     * @returns {Promise} Response with balance sheet data
     */
    async getBalanceSheetItems(reportId) {
        return this.request(`/financial/reports/${reportId}/balance-sheet`);
    }

    /**
     * Get income statement items for a specific report
     * @param {number} reportId - Report ID
     * @returns {Promise} Response with income statement data
     */
    async getIncomeStatementItems(reportId) {
        return this.request(`/financial/reports/${reportId}/income-statement`);
    }

    /**
     * Get cash flow items for a specific report
     * @param {number} reportId - Report ID
     * @returns {Promise} Response with cash flow data
     */
    async getCashFlowItems(reportId) {
        return this.request(`/financial/reports/${reportId}/cash-flow`);
    }

    // ===== EXTRACTION ENDPOINTS =====

    /**
     * Check if financial data has been extracted for a report
     * @param {number} reportId - Report ID
     * @returns {Promise} Response with extraction status
     */
    async checkExtractionStatus(reportId) {
        return this.request(`/extraction/check/${reportId}`);
    }

    /**
     * Extract financial data from a report (using default AI)
     * @param {number} reportId - Report ID
     * @returns {Promise} Response with extracted data
     */
    async extractFinancialData(reportId) {
        return this.request(`/extraction/extract/${reportId}`, {
            method: "POST",
        });
    }

    /**
     * Extract financial data using LM Studio
     * @param {number} reportId - Report ID
     * @returns {Promise} Response with extracted data
     */
    async extractFinancialDataLM(reportId) {
        return this.request(`/extraction/extract-lmstudio/${reportId}`, {
            method: "POST",
        });
    }

    // ===== UTILITY ENDPOINTS =====

    /**
     * Health check endpoint
     * @returns {Promise} Response with API health status
     */
    async healthCheck() {
        return this.request("/health");
    }
}

// Create global API client instance
const api = new APIClient();

// ===== UTILITY FUNCTIONS =====

/**
 * Format date string to human-readable format
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    if (!dateString) return "-";
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    } catch (error) {
        console.error("Error formatting date:", error);
        return dateString;
    }
}

/**
 * Format report period display
 * @param {string} reportType - "annual" or "quarterly"
 * @param {number} year - Report year
 * @param {number} quarter - Report quarter (1-4, optional)
 * @returns {string} Formatted period string
 */
function formatReportPeriod(reportType, year, quarter) {
    if (reportType === "annual") {
        return `${year} (Annual)`;
    } else if (reportType === "quarterly" && quarter) {
        return `Q${quarter}/${year}`;
    }
    return `${year}`;
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Toast type: "info", "success", "warning", "error"
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showToast(message, type = "info", duration = 3000) {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === "error" ? "#dc3545" : type === "success" ? "#28a745" : type === "warning" ? "#ffc107" : "#007bff"};
        color: white;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 10000;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;

    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => {
        toast.style.opacity = "1";
    }, 100);

    // Remove after duration
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Escape HTML to prevent XSS attacks
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
function escapeHtml(text) {
    if (!text) return "";
    const map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    };
    return String(text).replace(/[&<>"']/g, (m) => map[m]);
}

/**
 * Format number with thousand separators
 * @param {number} num - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number
 */
function formatNumber(num, decimals = 0) {
    if (num === null || num === undefined || isNaN(num)) return "-";
    try {
        return new Intl.NumberFormat("en-US", {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
        }).format(num);
    } catch (error) {
        return num.toString();
    }
}

/**
 * Format currency (VND)
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency
 */
function formatCurrency(amount) {
    if (amount === null || amount === undefined || isNaN(amount)) return "-";
    try {
        return new Intl.NumberFormat("vi-VN", {
            style: "currency",
            currency: "VND",
        }).format(amount);
    } catch (error) {
        return `${formatNumber(amount)} ₫`;
    }
}

/**
 * Format large numbers with K, M, B suffixes
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatCompactNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return "-";
    
    const absNum = Math.abs(num);
    const sign = num < 0 ? "-" : "";
    
    if (absNum >= 1e9) {
        return sign + (absNum / 1e9).toFixed(2) + "B";
    } else if (absNum >= 1e6) {
        return sign + (absNum / 1e6).toFixed(2) + "M";
    } else if (absNum >= 1e3) {
        return sign + (absNum / 1e3).toFixed(2) + "K";
    }
    return sign + absNum.toFixed(2);
}

/**
 * Debounce function to limit function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Check if API is in mock mode
 * @returns {boolean} True if mock mode is enabled
 */
function isMockMode() {
    return MOCK_MODE;
}

/**
 * Get current API base URL
 * @returns {string} API base URL
 */
function getApiBaseUrl() {
    return API_BASE_URL;
}

// Export for use in other scripts
if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        api,
        APIClient,
        formatDate,
        formatReportPeriod,
        showToast,
        escapeHtml,
        formatNumber,
        formatCurrency,
        formatCompactNumber,
        debounce,
        isMockMode,
        getApiBaseUrl,
    };
}
