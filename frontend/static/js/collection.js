/**
 * Data Collection Page Script
 * Handles dynamic symbol input, scraping operations, and console logging
 */

// Console logger class
class ConsoleLogger {
    constructor(logElementId, statsElements) {
        this.logElement = document.getElementById(logElementId);
        this.stats = {
            total: 0,
            success: 0,
            errors: 0,
        };
        this.statsElements = statsElements;
        this.logs = [];
    }

    log(type, message) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = { type, message, timestamp };
        this.logs.push(logEntry);

        // Update stats
        this.stats.total++;
        if (type === "success") this.stats.success++;
        if (type === "error") this.stats.errors++;

        this.render();
        this.updateStats();
    }

    info(message) {
        this.log("info", message);
    }

    success(message) {
        this.log("success", message);
    }

    error(message) {
        this.log("error", message);
    }

    warning(message) {
        this.log("warning", message);
    }

    clear() {
        this.logs = [];
        this.stats = { total: 0, success: 0, errors: 0 };
        this.render();
        this.updateStats();
    }

    render() {
        this.logElement.innerHTML = this.logs
            .map(
                (log) => `
            <div class="log-entry log-${log.type}">
                <span class="log-time">[${log.timestamp}]</span>
                <span class="log-type">[${log.type.toUpperCase()}]</span>
                <span class="log-message">${escapeHtml(log.message)}</span>
            </div>
        `,
            )
            .join("");

        // Auto scroll to bottom
        this.logElement.scrollTop = this.logElement.scrollHeight;
    }

    updateStats() {
        if (this.statsElements.total) {
            this.statsElements.total.textContent = this.stats.total;
        }
        if (this.statsElements.success) {
            this.statsElements.success.textContent = this.stats.success;
        }
        if (this.statsElements.errors) {
            this.statsElements.errors.textContent = this.stats.errors;
        }
    }
}

// Initialize logger
const logger = new ConsoleLogger("consoleLog", {
    total: document.getElementById("logTotal"),
    success: document.getElementById("logSuccess"),
    errors: document.getElementById("logErrors"),
});

// Dynamic Symbol Management
let symbolCounter = 0;

function createSymbolRow(index) {
    const row = document.createElement("div");
    row.className = "symbol-row";
    row.dataset.index = index;
    row.innerHTML = `
        <input 
            type="text" 
            class="input-field symbol-input" 
            placeholder="Enter symbol (e.g., FPT)"
        >
        <select class="input-field source-select">
            <option value="cafef">CafeF</option>
            <option value="vietstock" disabled>VietStockFinance (Coming Soon)</option>
        </select>
        <button class="btn-icon-action btn-remove" title="Remove" onclick="removeSymbolRow(${index})">
            <span>✕</span>
        </button>
    `;
    return row;
}

function addSymbolRow() {
    symbolCounter++;
    const container = document.getElementById("symbolsContainer");
    const newRow = createSymbolRow(symbolCounter);
    container.appendChild(newRow);

    // Enable remove buttons if more than one row
    updateRemoveButtons();
}

function removeSymbolRow(index) {
    const rows = document.querySelectorAll(".symbol-row");

    // Prevent removing if only one row left
    if (rows.length <= 1) {
        return;
    }

    const row = document.querySelector(`.symbol-row[data-index="${index}"]`);
    if (row) {
        row.classList.add("removing");
        setTimeout(() => {
            row.remove();
            updateRemoveButtons();
        }, 300);
    }
}

function updateRemoveButtons() {
    const rows = document.querySelectorAll(".symbol-row");
    const removeButtons = document.querySelectorAll(".btn-remove");

    removeButtons.forEach((btn, index) => {
        btn.disabled = rows.length === 1;
    });
}

function getSymbolsData() {
    const rows = document.querySelectorAll(".symbol-row");
    const symbols = [];

    rows.forEach((row) => {
        const input = row.querySelector(".symbol-input");
        const select = row.querySelector(".source-select");
        const symbol = input.value.trim().toUpperCase();
        const source = select.value;

        if (symbol) {
            symbols.push({ symbol, source });
        }
    });

    return symbols;
}

// Scraping state management
let isScraping = false;

function setScrapingState(scraping) {
    isScraping = scraping;
    document.getElementById("startScrapeBtn").disabled = scraping;
    document.getElementById("stopScrapeBtn").disabled = !scraping;
    document.getElementById("addSymbolBtn").disabled = scraping;

    const inputs = document.querySelectorAll(".symbol-input, .source-select");
    inputs.forEach((input) => (input.disabled = scraping));
}

// Handle scraping
async function handleStartScrape() {
    const symbolsData = getSymbolsData();

    if (symbolsData.length === 0) {
        logger.error("No symbols entered");
        showToast("error", "Please enter at least one symbol");
        return;
    }

    // Check if any symbol uses unsupported source
    const unsupported = symbolsData.filter((s) => s.source !== "cafef");
    if (unsupported.length > 0) {
        logger.error(
            `Unsupported source: ${unsupported.map((s) => s.source).join(", ")}`,
        );
        showToast("error", "Only CafeF source is currently supported");
        return;
    }

    const headless = document.getElementById("headlessMode").checked;

    setScrapingState(true);
    logger.info(`Starting scrape for ${symbolsData.length} symbol(s)...`);

    try {
        if (symbolsData.length === 1) {
            // Single scrape
            const { symbol } = symbolsData[0];
            logger.info(`Scraping ${symbol}...`);

            const result = await api.scrapeSingle(symbol, headless);

            if (result.success) {
                logger.success(
                    `✓ ${symbol}: ${result.message} (${result.reports_count} reports, ${result.created_count} created, ${result.updated_count} updated)`,
                );
                showToast("success", `Successfully scraped ${symbol}`);
            } else {
                logger.error(`✗ ${symbol}: ${result.message}`);
                showToast("error", `Failed to scrape ${symbol}`);
            }
        } else {
            // Bulk scrape
            const symbols = symbolsData.map((s) => s.symbol);
            logger.info(`Bulk scraping ${symbols.length} symbols...`);

            const result = await api.scrapeBulk(symbols, headless);

            logger.info(
                `Bulk scrape completed: ${result.successful_symbols}/${result.total_symbols} successful`,
            );

            if (result.results) {
                result.results.forEach((r) => {
                    if (r.success) {
                        logger.success(
                            `✓ ${r.symbol}: ${r.reports_count} reports (${r.created_count} created, ${r.updated_count} updated)`,
                        );
                    } else {
                        logger.error(`✗ ${r.symbol}: ${r.message}`);
                    }
                });
            }

            showToast(
                "success",
                `Completed: ${result.successful_symbols}/${result.total_symbols} symbols`,
            );
        }
    } catch (error) {
        logger.error(`Scraping failed: ${error.message}`);
        showToast("error", "Scraping operation failed");
    } finally {
        setScrapingState(false);
    }
}

function handleStopScrape() {
    logger.warning("Stop requested - completing current operation...");
    setScrapingState(false);
}

function handleClearLogs() {
    logger.clear();
    logger.info("Console cleared");
}

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
    // Add symbol button
    document
        .getElementById("addSymbolBtn")
        .addEventListener("click", addSymbolRow);

    // Scrape buttons
    document
        .getElementById("startScrapeBtn")
        .addEventListener("click", handleStartScrape);
    document
        .getElementById("stopScrapeBtn")
        .addEventListener("click", handleStopScrape);

    // Clear logs button
    document
        .getElementById("clearLogsBtn")
        .addEventListener("click", handleClearLogs);

    // Settings modal
    const settingsModal = document.getElementById("settingsModal");
    const settingsBtn = document.getElementById("settingsBtn");
    const settingsModalClose = document.getElementById("settingsModalClose");
    const saveSettingsBtn = document.getElementById("saveSettingsBtn");

    settingsBtn.addEventListener("click", () => {
        settingsModal.classList.add("show");
    });

    settingsModalClose.addEventListener("click", () => {
        settingsModal.classList.remove("show");
    });

    saveSettingsBtn.addEventListener("click", () => {
        settingsModal.classList.remove("show");
        showToast("success", "Settings saved");
        logger.info("Settings updated");
    });

    settingsModal.addEventListener("click", (e) => {
        if (e.target === settingsModal) {
            settingsModal.classList.remove("show");
        }
    });

    // Initialize
    updateRemoveButtons();
    logger.info("System initialized and ready");
    logger.info("Add symbols and click Start to begin scraping");
});
