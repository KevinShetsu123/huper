/**
 * Report Detail Page Script
 * Displays detailed financial information for a specific report
 */

// Get report ID from URL
const urlParams = new URLSearchParams(window.location.search);
const reportId = urlParams.get("id");

// Helper function
function escapeHtml(text) {
    if (!text) return text;
    const map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    };
    return String(text).replace(/[&<>"']/g, (m) => map[m]);
}

// Text formatting functions
function toTitleCase(text, symbol = null) {
    if (!text) return text;

    // Convert to lowercase first
    text = text.toLowerCase();

    // Split into words
    const words = text.split(" ");

    // Capitalize first letter of each word
    const titleCased = words.map((word) => {
        // Check if this word is the symbol (case-insensitive match)
        if (symbol && word.toLowerCase() === symbol.toLowerCase()) {
            return symbol.toUpperCase();
        }
        // Capitalize first letter
        return word.charAt(0).toUpperCase() + word.slice(1);
    });

    return titleCased.join(" ");
}

function formatCompanyName(companyName, symbol) {
    if (!companyName) return companyName;

    // Use title case with symbol uppercase handling
    return toTitleCase(companyName, symbol);
}

function formatReportName(reportName, symbol) {
    if (!reportName) return reportName;

    // Use title case with symbol uppercase handling
    return toTitleCase(reportName, symbol);
}

function formatReportPeriod(reportType, year, quarter) {
    if (reportType === "annual") {
        return `${year} (Annual)`;
    } else if (reportType === "quarterly" && quarter) {
        return `Q${quarter}/${year}`;
    }
    return `${year}`;
}

// Load report data
async function loadReportData() {
    if (!reportId) {
        showToast("No report ID provided", "error");
        setTimeout(() => (window.location.href = "/management"), 2000);
        return;
    }

    console.log("Starting to load report data for ID:", reportId);

    try {
        const result = await api.getReportById(reportId);
        console.log("Report info result:", result);

        if (result.success) {
            const report = result.data;
            displayReportInfo(report);

            // Check extraction status (if function exists)
            if (typeof checkAndShowExtractionButton === "function") {
                await checkAndShowExtractionButton(reportId);
            }

            // Load financial data
            await loadBalanceSheet(reportId);
            await loadIncomeStatement(reportId);
            await loadCashFlow(reportId);
        } else {
            showToast(
                "Failed to load report data: " +
                    (result.error || "Unknown error"),
                "error",
            );
            console.error("Report load failed:", result);
        }
    } catch (error) {
        showToast("Error loading report: " + error.message, "error");
        console.error("Exception loading report:", error);
    }
}

function displayReportInfo(report) {
    const symbol = report.symbol.toUpperCase();

    // Update page title
    document.getElementById("pageTitle").textContent =
        `${symbol} - Financial Report`;
    document.title = `${symbol} - Financial Report - Hyper Data Lab`;

    // Update info fields
    document.getElementById("infoSymbol").textContent = symbol;
    document.getElementById("infoCompany").textContent = formatCompanyName(
        report.company_name,
        symbol,
    );
    document.getElementById("infoReportName").textContent = formatReportName(
        report.report_name,
        symbol,
    );
    document.getElementById("infoType").innerHTML =
        `<span class="badge badge-${report.report_type}">${toTitleCase(report.report_type)}</span>`;
    document.getElementById("infoPeriod").textContent = formatReportPeriod(
        report.report_type,
        report.report_year,
        report.report_quarter,
    );
    document.getElementById("infoAudited").innerHTML =
        report.is_audited ?
            '<span class="badge badge-success">Yes</span>'
        :   '<span class="badge badge-muted">No</span>';
    document.getElementById("infoReviewed").innerHTML =
        report.is_reviewed ?
            '<span class="badge badge-success">Yes</span>'
        :   '<span class="badge badge-muted">No</span>';

    // Set URL link if element exists
    const urlLink = document.getElementById("infoUrl");
    if (urlLink && report.report_url) {
        urlLink.href = report.report_url;
    }
}

// Tab switching
function switchFinancialTab(tabName) {
    // Update tab buttons
    document.querySelectorAll(".financial-tab").forEach((tab) => {
        tab.classList.remove("active");
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add("active");

    // Update tab content
    document.querySelectorAll(".tab-pane").forEach((pane) => {
        pane.classList.remove("active");
    });
    document.getElementById(`${tabName}-content`).classList.add("active");
}

// Load financial statements
async function loadBalanceSheet(reportId) {
    const container = document.getElementById("balance-sheet-content");
    container.innerHTML = '<div class="loading">Loading balance sheet...</div>';

    console.log("Loading balance sheet for report", reportId);
    const result = await api.getBalanceSheetItems(reportId);
    console.log("Balance sheet result:", result);

    if (result.success && result.data.length > 0) {
        container.innerHTML = renderFinancialTable(
            result.data,
            "Balance Sheet",
        );
    } else {
        container.innerHTML =
            '<div class="text-center">No balance sheet data available</div>';
    }
}

async function loadIncomeStatement(reportId) {
    const container = document.getElementById("income-statement-content");
    container.innerHTML =
        '<div class="loading">Loading income statement...</div>';

    console.log("Loading income statement for report", reportId);
    const result = await api.getIncomeStatementItems(reportId);
    console.log("Income statement result:", result);

    if (result.success && result.data.length > 0) {
        container.innerHTML = renderFinancialTable(
            result.data,
            "Income Statement",
        );
    } else {
        container.innerHTML =
            '<div class="text-center">No income statement data available</div>';
    }
}

async function loadCashFlow(reportId) {
    const container = document.getElementById("cash-flow-content");
    container.innerHTML = '<div class="loading">Loading cash flow...</div>';

    console.log("Loading cash flow for report", reportId);
    const result = await api.getCashFlowItems(reportId);
    console.log("Cash flow result:", result);

    if (result.success && result.data.length > 0) {
        container.innerHTML = renderFinancialTable(result.data, "Cash Flow");
    } else {
        container.innerHTML =
            '<div class="text-center">No cash flow data available</div>';
    }
}

function renderFinancialTable(items, title) {
    if (!items || items.length === 0) {
        return '<div class="text-center" style="padding: 2rem; color: #a1a1aa;">No data available</div>';
    }

    const html = `
        <div class="table-wrapper">
            <table class="financial-table">
                <thead>
                    <tr>
                        <th style="text-align: left; min-width: 300px;">Item Name</th>
                        <th style="text-align: center; width: 100px;">Code</th>
                        <th style="text-align: right; width: 180px;">Value</th>
                    </tr>
                </thead>
                <tbody>
                    ${items
                        .map((item) => {
                            const indentLevel = (item.level - 1) * 20;
                            const itemName = item.item_name || "N/A";
                            const displayValue = item.item_value * item.sign;
                            const isNegative = displayValue < 0;

                            return `
                            <tr data-level="${item.level}">
                                <td style="padding-left: ${indentLevel}px; font-weight: ${item.level === 1 ? "600" : "400"};">
                                    ${escapeHtml(itemName)}
                                </td>
                                <td style="text-align: center;">${item.item_code || "-"}</td>
                                <td style="text-align: right; color: ${isNegative ? "#ef4444" : "inherit"};">
                                    ${formatNumber(displayValue)}
                                </td>
                            </tr>
                        `;
                        })
                        .join("")}
                </tbody>
            </table>
        </div>
    `;

    return html;
}

function formatNumber(value) {
    if (value === null || value === undefined) return "-";
    return new Intl.NumberFormat("vi-VN").format(value);
}

function showToast(message, type = "info") {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Simple toast implementation
    const toast = document.createElement("div");
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === "error" ? "#ef4444" : "#22c55e"};
        color: white;
        border-radius: 6px;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = "slideOut 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
    // Tab switching
    document.querySelectorAll(".financial-tab").forEach((tab) => {
        tab.addEventListener("click", (e) => {
            switchFinancialTab(e.target.dataset.tab);
        });
    });

    // Load data
    loadReportData();
});
