// Data Management Page Script

// State
let currentData = [];
let filteredData = [];
let deleteTargetId = null;

// DOM Elements
const filterSymbol = document.getElementById("filterSymbol");
const filterType = document.getElementById("filterType");
const filterYear = document.getElementById("filterYear");
const filterQuarter = document.getElementById("filterQuarter");
const filterAssurance = document.getElementById("filterAssurance");
const filterLimit = document.getElementById("filterLimit");
const applyFiltersBtn = document.getElementById("applyFiltersBtn");
const clearFiltersBtn = document.getElementById("clearFiltersBtn");
const dataTableBody = document.getElementById("dataTableBody");
const deleteModal = document.getElementById("deleteModal");
const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
const cancelDeleteBtn = document.getElementById("cancelDeleteBtn");
const modalClose = document.querySelector(".modal-close");

// Event Listeners
applyFiltersBtn.addEventListener("click", loadData);
clearFiltersBtn.addEventListener("click", clearFilters);
confirmDeleteBtn.addEventListener("click", confirmDelete);
cancelDeleteBtn.addEventListener("click", closeModal);
modalClose.addEventListener("click", closeModal);

// Disable Quarter when Report Type is Annual
filterType.addEventListener("change", () => {
    if (filterType.value === "annual") {
        filterQuarter.disabled = true;
        filterQuarter.value = "";
    } else {
        filterQuarter.disabled = false;
    }
});

// Close modal on outside click
deleteModal.addEventListener("click", (e) => {
    if (e.target === deleteModal) closeModal();
});

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    loadData();
    loadStats();

    // Initialize Quarter field state
    if (filterType.value === "annual") {
        filterQuarter.disabled = true;
    }
});

async function loadData() {
    const params = {
        symbol: filterSymbol.value.trim(),
        report_type: filterType.value,
        report_year: filterYear.value ? parseInt(filterYear.value) : null,
        limit: parseInt(filterLimit.value),
    };

    showTableLoading();

    const result = await api.getReports(params);

    if (result.success) {
        currentData = result.data;
        filteredData = currentData;
        renderTable();
        updateTableInfo();
        showToast(`Loaded ${currentData.length} reports`, "success");
    } else {
        showTableError(result.error);
        showToast("Failed to load data", "error");
    }
}

async function loadStats() {
    const result = await api.getStats();

    if (result.success) {
        document.getElementById("totalReports").textContent =
            result.data.total_reports || 0;
    }

    // Load detailed stats
    const allResult = await api.getReports({ limit: 1000 });
    if (allResult.success) {
        const data = allResult.data;
        const quarterly = data.filter(
            (r) => r.report_type === "quarterly",
        ).length;
        const annual = data.filter((r) => r.report_type === "annual").length;
        const audited = data.filter((r) => r.is_audited).length;

        document.getElementById("quarterlyReports").textContent = quarterly;
        document.getElementById("annualReports").textContent = annual;
        document.getElementById("auditedReports").textContent = audited;
    }
}

function renderTable() {
    if (filteredData.length === 0) {
        dataTableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center">No data found</td>
            </tr>
        `;
        return;
    }

    const html = filteredData
        .map(
            (report) => `
        <tr class="table-row-clickable" onclick="viewReportDetails(${report.id})">
            <td><span class="badge">${escapeHtml(report.symbol.toUpperCase())}</span></td>
            <td>${escapeHtml(toTitleCase(report.company_name, report.symbol))}</td>
            <td>${escapeHtml(toTitleCase(report.report_name, report.symbol))}</td>
            <td><span class="badge badge-${report.report_type}">${toTitleCase(report.report_type)}</span></td>
            <td>${report.report_year}</td>
            <td>${report.report_quarter || "-"}</td>
            <td>${report.is_audited ? '<span class="badge badge-success">Yes</span>' : '<span class="badge badge-muted">No</span>'}</td>
            <td>${report.is_reviewed ? '<span class="badge badge-success">Yes</span>' : '<span class="badge badge-muted">No</span>'}</td>
        </tr>
    `,
        )
        .join("");

    dataTableBody.innerHTML = html;
}

function updateTableInfo() {
    document.getElementById("showingCount").textContent = filteredData.length;
}

function showTableLoading() {
    dataTableBody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center">
                <div class="loading">Loading data...</div>
            </td>
        </tr>
    `;
}

function showTableError(error) {
    dataTableBody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center error">
                Error loading data: ${escapeHtml(error)}
            </td>
        </tr>
    `;
}

function clearFilters() {
    filterSymbol.value = "";
    filterType.value = "";
    filterYear.value = "";
    filterQuarter.value = "";
    filterAssurance.value = "";
    filterLimit.value = "100";
    loadData();
}

// Global functions for button onclick
window.viewReport = async function (id) {
    const result = await api.getReportById(id);

    if (result.success) {
        const report = result.data;
        alert(
            `Report Details:\n\n` +
                `ID: ${report.id}\n` +
                `Symbol: ${report.symbol}\n` +
                `Company: ${report.company_name}\n` +
                `Report: ${report.report_name}\n` +
                `Type: ${report.report_type}\n` +
                `Period: ${formatReportPeriod(report.report_type, report.report_year, report.report_quarter)}\n` +
                `Audited: ${report.is_audited ? "Yes" : "No"}\n` +
                `Reviewed: ${report.is_reviewed ? "Yes" : "No"}\n` +
                `URL: ${report.report_url}`,
        );
    } else {
        showToast("Failed to load report details", "error");
    }
};

window.deleteReport = function (id) {
    deleteTargetId = id;
    const report = filteredData.find((r) => r.id === id);

    if (report) {
        document.getElementById("deleteDetail").textContent =
            `${report.symbol} - ${report.report_name} (${formatReportPeriod(report.report_type, report.report_year, report.report_quarter)})`;
    }

    deleteModal.classList.add("show");
};

async function confirmDelete() {
    if (!deleteTargetId) return;

    const result = await api.deleteReport(deleteTargetId);

    if (result.success) {
        showToast("Report deleted successfully", "success");
        closeModal();
        loadData();
        loadStats();
    } else {
        showToast("Failed to delete report", "error");
    }
}

function closeModal() {
    deleteModal.classList.remove("show");
    deleteTargetId = null;
}

function exportToCSV() {
    if (filteredData.length === 0) {
        showToast("No data to export", "warning");
        return;
    }

    const headers = [
        "ID",
        "Symbol",
        "Company",
        "Report Name",
        "Type",
        "Year",
        "Quarter",
        "Audited",
        "Reviewed",
        "URL",
    ];
    const rows = filteredData.map((report) => [
        report.id,
        report.symbol,
        report.company_name,
        report.report_name,
        report.report_type,
        report.report_year,
        report.report_quarter || "",
        report.is_audited ? "Yes" : "No",
        report.is_reviewed ? "Yes" : "No",
        report.report_url,
    ]);

    const csvContent = [
        headers.join(","),
        ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);

    link.setAttribute("href", url);
    link.setAttribute(
        "download",
        `financial_reports_${new Date().toISOString().split("T")[0]}.csv`,
    );
    link.style.visibility = "hidden";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast("Data exported successfully", "success");
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

// Financial Detail Modal Functions
window.viewReportDetails = function (id) {
    // Navigate to detail page
    window.location.href = `/detail?id=${id}`;
};
