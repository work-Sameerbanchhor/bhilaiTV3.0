// BhilaiTV // Terminal UI, Splash Screen & Command Engine Controller
(function() {
    // Application State
    let currentPage = 1;
    let totalPages = 1;
    let currentQuery = "";
    let currentFilter = "ALL"; // ALL, MOVIES, SERIES
    let activeCliFilter = "";  // e.g. "1080p", "hindi", "4k"
    let currentItems = [];
    let searchDebounceTimer = null;
    let selectedSuggestionIndex = -1;

    // User Preferences (Default: MONOCHROME B&W)
    const storedTheme = localStorage.getItem("bhilai_theme");
    const isExplicit = localStorage.getItem("bhilai_theme_explicit");
    const activeTheme = (storedTheme === "matrix" && !isExplicit) ? "mono" : (storedTheme || "mono");

    const settings = {
        theme: activeTheme,
        preferredServer: localStorage.getItem("bhilai_server") || "server1",
        perPage: parseInt(localStorage.getItem("bhilai_perpage") || "24", 10)
    };

    // Terminal Commands Registry
    const COMMANDS = [
        {
            cmd: "/settings",
            aliases: ["/config", "/cfg"],
            syntax: "/settings",
            desc: "Open terminal settings & server preferences",
            badge: "CONFIG",
            run: () => openSettingsModal()
        },
        {
            cmd: "/filter",
            aliases: ["/f"],
            syntax: "/filter <1080p|720p|4k|hindi|clear>",
            desc: "Filter releases by quality, audio, or clear filter",
            badge: "FILTER",
            run: (args) => handleFilterCommand(args)
        },
        {
            cmd: "/theme",
            aliases: ["/color", "/palette"],
            syntax: "/theme <0|matrix|amber|cyan|magenta>",
            desc: "Switch CRT palette (/theme 0 for pure black & white)",
            badge: "PALETTE",
            run: (args) => handleThemeCommand(args)
        },
        {
            cmd: "/latest",
            aliases: ["/recent", "/home"],
            syntax: "/latest",
            desc: "Reset query and show latest discoveries",
            badge: "CATALOG",
            run: () => handleLatestCommand()
        },
        {
            cmd: "/clear",
            aliases: ["/cls", "/reset"],
            syntax: "/clear",
            desc: "Clear search prompt and active filters",
            badge: "CLI",
            run: () => handleClearCommand()
        },
        {
            cmd: "/stats",
            aliases: ["/info", "/ping"],
            syntax: "/stats",
            desc: "Display gateway status and resolver telemetry",
            badge: "STATUS",
            run: () => handleStatsCommand()
        },
        {
            cmd: "/help",
            aliases: ["/?", "/man"],
            syntax: "/help",
            desc: "Display interactive command reference",
            badge: "HELP",
            run: () => openHelpModal()
        }
    ];

    // DOM Elements
    const splashScreen = document.getElementById("splash-screen");
    const splashProgressBar = document.getElementById("splash-progress-bar");
    const splashStatusText = document.getElementById("splash-status-text");
    const splashPercentage = document.getElementById("splash-percentage");

    const searchInput = document.getElementById("search-input");
    const cmdSuggestions = document.getElementById("cmd-suggestions");
    const cmdList = document.getElementById("cmd-list");
    const releasesGrid = document.getElementById("releases-grid");
    const gridStatus = document.getElementById("grid-status");
    const resultsCount = document.getElementById("results-count");
    const btnPrev = document.getElementById("btn-prev");
    const btnNext = document.getElementById("btn-next");
    const pageIndicator = document.getElementById("page-indicator");
    const filterBtns = document.querySelectorAll(".filter-btn");
    
    // Active Filter Indicator
    const activeFilterIndicator = document.getElementById("active-filter-indicator");
    const activeFilterLabel = document.getElementById("active-filter-label");
    const clearFilterBtn = document.getElementById("clear-filter-btn");

    // Modals
    const detailModal = document.getElementById("detail-modal");
    const modalCloseBtn = document.getElementById("modal-close-btn");
    const modalTitle = document.getElementById("modal-title");
    const modalMeta = document.getElementById("modal-meta");
    const modalBody = document.getElementById("modal-body");

    const settingsModal = document.getElementById("settings-modal");
    const settingsCloseBtn = document.getElementById("settings-close-btn");

    const helpModal = document.getElementById("help-modal");
    const helpCloseBtn = document.getElementById("help-close-btn");

    const toast = document.getElementById("toast");

    // Initialize
    document.addEventListener("DOMContentLoaded", () => {
        applyTheme(settings.theme);
        updateSettingsPillsUI();
        initSplashScreen();
        loadReleases();
        bindEvents();
    });

    // --- 4-SECOND SMOOTH SPLASH SCREEN PROGRESS ENGINE ---
    function initSplashScreen() {
        if (!splashScreen) return;

        const DURATION = 4000; // 4.0 seconds
        const startTime = performance.now();
        let isDone = false;

        const statusStages = [
            { pct: 0, text: "> INITIALIZING TERMINAL KERNEL..." },
            { pct: 20, text: "> ESTABLISHING GATEWAY LINK..." },
            { pct: 45, text: "> SYNCING 15,450+ CATALOG RELEASES..." },
            { pct: 70, text: "> MOUNTING ZERO-AD STREAM RESOLVERS..." },
            { pct: 90, text: "> OPTIMIZING CRT RENDER ENGINE..." },
            { pct: 100, text: "> SYSTEM ONLINE // ACCESS GRANTED" }
        ];

        function updateProgress(now) {
            if (isDone) return;

            const elapsed = now - startTime;
            const progress = Math.min(elapsed / DURATION, 1);
            const currentPct = Math.floor(progress * 100);

            if (splashProgressBar) {
                splashProgressBar.style.width = `${progress * 100}%`;
            }
            if (splashPercentage) {
                splashPercentage.textContent = `${currentPct}%`;
            }

            // Update status text based on current percentage
            for (let i = statusStages.length - 1; i >= 0; i--) {
                if (currentPct >= statusStages[i].pct) {
                    if (splashStatusText) {
                        splashStatusText.textContent = statusStages[i].text;
                    }
                    break;
                }
            }

            if (progress < 1) {
                requestAnimationFrame(updateProgress);
            } else {
                finishSplash();
            }
        }

        function finishSplash() {
            if (isDone) return;
            isDone = true;

            if (splashProgressBar) splashProgressBar.style.width = "100%";
            if (splashPercentage) splashPercentage.textContent = "100%";
            if (splashStatusText) splashStatusText.textContent = "> SYSTEM ONLINE // ACCESS GRANTED";

            setTimeout(() => {
                splashScreen.classList.add("fade-out");
                setTimeout(() => {
                    if (splashScreen.parentNode) {
                        splashScreen.parentNode.removeChild(splashScreen);
                    }
                }, 550);
            }, 250);
        }

        // Tap or press to skip splash instantly
        splashScreen.addEventListener("click", finishSplash);
        document.addEventListener("keydown", function skipOnKey(e) {
            if (!isDone && (e.key === "Enter" || e.key === " " || e.key === "Escape")) {
                finishSplash();
                document.removeEventListener("keydown", skipOnKey);
            }
        });

        requestAnimationFrame(updateProgress);
    }

    function bindEvents() {
        // Search Input Events
        searchInput.addEventListener("input", (e) => {
            const val = e.target.value;
            if (val.startsWith("/")) {
                showCommandSuggestions(val);
            } else {
                hideCommandSuggestions();
                clearTimeout(searchDebounceTimer);
                searchDebounceTimer = setTimeout(() => {
                    currentQuery = val.trim();
                    currentPage = 1;
                    loadReleases();
                }, 350);
            }
        });

        searchInput.addEventListener("keydown", (e) => {
            const val = searchInput.value;

            // Handle navigation inside command suggestions
            if (cmdSuggestions.classList.contains("active")) {
                const items = cmdList.querySelectorAll(".cmd-item");
                if (e.key === "ArrowDown") {
                    e.preventDefault();
                    if (items.length > 0) {
                        selectedSuggestionIndex = (selectedSuggestionIndex + 1) % items.length;
                        highlightSuggestion(items);
                    }
                    return;
                } else if (e.key === "ArrowUp") {
                    e.preventDefault();
                    if (items.length > 0) {
                        selectedSuggestionIndex = (selectedSuggestionIndex - 1 + items.length) % items.length;
                        highlightSuggestion(items);
                    }
                    return;
                } else if (e.key === "Tab") {
                    e.preventDefault();
                    if (selectedSuggestionIndex >= 0 && items[selectedSuggestionIndex]) {
                        const selectedCmd = items[selectedSuggestionIndex].getAttribute("data-cmd");
                        searchInput.value = selectedCmd + " ";
                        showCommandSuggestions(searchInput.value);
                    }
                    return;
                } else if (e.key === "Escape") {
                    hideCommandSuggestions();
                    return;
                }
            }

            if (e.key === "Enter") {
                clearTimeout(searchDebounceTimer);
                hideCommandSuggestions();

                if (val.startsWith("/")) {
                    e.preventDefault();
                    executeSlashCommand(val.trim());
                } else {
                    currentQuery = val.trim();
                    currentPage = 1;
                    loadReleases();
                }
            }
        });

        // Global Keyboard Shortcuts
        document.addEventListener("keydown", (e) => {
            if (e.key === "/" && document.activeElement !== searchInput) {
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            } else if (e.key === "Escape") {
                closeAllModals();
                hideCommandSuggestions();
            }
        });

        // Clear Filter Button
        if (clearFilterBtn) {
            clearFilterBtn.addEventListener("click", () => {
                handleFilterCommand("clear");
            });
        }

        // Pagination
        btnPrev.addEventListener("click", () => {
            if (currentPage > 1) {
                currentPage--;
                loadReleases();
                window.scrollTo({ top: 0, behavior: "smooth" });
            }
        });

        btnNext.addEventListener("click", () => {
            if (currentPage < totalPages) {
                currentPage++;
                loadReleases();
                window.scrollTo({ top: 0, behavior: "smooth" });
            }
        });

        // Filter Pills
        filterBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                filterBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                currentFilter = btn.getAttribute("data-filter");
                renderGrid();
            });
        });

        // Modal Close Events
        modalCloseBtn.addEventListener("click", () => detailModal.classList.remove("active"));
        settingsCloseBtn.addEventListener("click", () => settingsModal.classList.remove("active"));
        helpCloseBtn.addEventListener("click", () => helpModal.classList.remove("active"));

        [detailModal, settingsModal, helpModal].forEach(modal => {
            modal.addEventListener("click", (e) => {
                if (e.target === modal) modal.classList.remove("active");
            });
        });

        // Settings Interactive Pills
        document.querySelectorAll("#theme-pills .settings-pill-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const theme = btn.getAttribute("data-theme");
                applyTheme(theme);
                updateSettingsPillsUI();
                showToast(`[OK] Theme switched to: ${theme === "mono" ? "MONOCHROME (B&W)" : theme.toUpperCase()}`);
            });
        });

        document.querySelectorAll("#server-pills .settings-pill-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                settings.preferredServer = btn.getAttribute("data-server");
                localStorage.setItem("bhilai_server", settings.preferredServer);
                updateSettingsPillsUI();
                showToast(`[OK] Preferred server set to: ${settings.preferredServer.toUpperCase()}`);
            });
        });

        document.querySelectorAll("#perpage-pills .settings-pill-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                settings.perPage = parseInt(btn.getAttribute("data-perpage"), 10);
                localStorage.setItem("bhilai_perpage", settings.perPage.toString());
                updateSettingsPillsUI();
                showToast(`[OK] Page size set to: ${settings.perPage}`);
                currentPage = 1;
                loadReleases();
            });
        });
    }

    // --- COMMAND ENGINE & PARSER ---

    function showCommandSuggestions(inputVal) {
        const query = inputVal.toLowerCase().trim();
        const matches = COMMANDS.filter(c => {
            return c.cmd.startsWith(query) || 
                   c.aliases.some(a => a.startsWith(query)) ||
                   query.startsWith(c.cmd);
        });

        if (matches.length === 0) {
            hideCommandSuggestions();
            return;
        }

        cmdList.innerHTML = matches.map((c, idx) => `
            <div class="cmd-item ${idx === selectedSuggestionIndex ? 'selected' : ''}" data-cmd="${c.cmd}" onclick="window.BhilaiApp.selectCommand('${c.cmd}')">
                <div style="display: flex; align-items: center;">
                    <span class="cmd-name">${c.syntax}</span>
                    <span class="cmd-desc">${c.desc}</span>
                </div>
                <span class="cmd-badge">${c.badge}</span>
            </div>
        `).join("");

        selectedSuggestionIndex = 0;
        highlightSuggestion(cmdList.querySelectorAll(".cmd-item"));
        cmdSuggestions.classList.add("active");
    }

    function highlightSuggestion(items) {
        items.forEach((item, idx) => {
            if (idx === selectedSuggestionIndex) {
                item.classList.add("selected");
                item.scrollIntoView({ block: "nearest" });
            } else {
                item.classList.remove("selected");
            }
        });
    }

    function hideCommandSuggestions() {
        cmdSuggestions.classList.remove("active");
        selectedSuggestionIndex = -1;
    }

    function executeSlashCommand(rawInput) {
        const parts = rawInput.trim().split(/\s+/);
        const cmdName = parts[0].toLowerCase();
        const args = parts.slice(1).join(" ");

        const matched = COMMANDS.find(c => c.cmd === cmdName || c.aliases.includes(cmdName));

        if (matched) {
            matched.run(args);
        } else {
            showToast(`[!] Unknown command: ${cmdName}. Type /help for cheat sheet.`);
        }
    }

    // Command Handlers
    function handleFilterCommand(args) {
        const tag = (args || "").trim().toLowerCase();

        if (!tag || tag === "clear" || tag === "reset" || tag === "none") {
            activeCliFilter = "";
            activeFilterIndicator.style.display = "none";
            renderGrid();
            showToast("[OK] Active filter cleared");
            searchInput.value = "";
            return;
        }

        activeCliFilter = tag.toUpperCase();
        activeFilterLabel.textContent = activeCliFilter;
        activeFilterIndicator.style.display = "block";
        renderGrid();
        showToast(`[OK] Filter set to: ${activeCliFilter}`);
        searchInput.value = "";
    }

    function handleThemeCommand(args) {
        let target = (args || "").trim().toLowerCase();

        // Support /theme 0, /theme mono, /theme bw, /theme black
        if (target === "0" || target === "mono" || target === "bw" || target === "black" || target === "white") {
            target = "mono";
        }

        const validThemes = ["mono", "matrix", "amber", "cyan", "magenta"];

        if (validThemes.includes(target)) {
            applyTheme(target);
            updateSettingsPillsUI();
            const label = target === "mono" ? "MONOCHROME (BLACK & WHITE)" : target.toUpperCase();
            showToast(`[OK] Theme switched to: ${label}`);
            searchInput.value = "";
        } else {
            showToast(`[!] Usage: /theme <0|matrix|amber|cyan|magenta>`);
        }
    }

    function handleLatestCommand() {
        currentQuery = "";
        searchInput.value = "";
        activeCliFilter = "";
        activeFilterIndicator.style.display = "none";
        currentFilter = "ALL";
        filterBtns.forEach(b => b.classList.toggle("active", b.getAttribute("data-filter") === "ALL"));
        currentPage = 1;
        loadReleases();
        showToast("[OK] Reloaded latest discoveries");
    }

    function handleClearCommand() {
        searchInput.value = "";
        currentQuery = "";
        activeCliFilter = "";
        activeFilterIndicator.style.display = "none";
        hideCommandSuggestions();
        renderGrid();
        showToast("[OK] Prompt & CLI filters cleared");
    }

    function handleStatsCommand() {
        showToast(`[GATEWAY] 15,450+ Releases | Servers: R2 + FastCloud | Mode: ONLINE`);
    }

    // Theme Management
    function applyTheme(themeName) {
        document.body.classList.remove("theme-mono", "theme-0", "theme-amber", "theme-cyan", "theme-magenta", "theme-matrix");
        if (themeName === "mono" || themeName === "0") {
            document.body.classList.add("theme-mono");
        } else if (themeName === "matrix") {
            document.body.classList.add("theme-matrix");
        } else {
            document.body.classList.add("theme-" + themeName);
        }
        settings.theme = themeName === "0" ? "mono" : themeName;
        localStorage.setItem("bhilai_theme", settings.theme);
    }

    function updateSettingsPillsUI() {
        document.querySelectorAll("#theme-pills .settings-pill-btn").forEach(btn => {
            const btnTheme = btn.getAttribute("data-theme");
            btn.classList.toggle("active", btnTheme === settings.theme || (settings.theme === "mono" && btnTheme === "mono"));
        });
        document.querySelectorAll("#server-pills .settings-pill-btn").forEach(btn => {
            btn.classList.toggle("active", btn.getAttribute("data-server") === settings.preferredServer);
        });
        document.querySelectorAll("#perpage-pills .settings-pill-btn").forEach(btn => {
            btn.classList.toggle("active", parseInt(btn.getAttribute("data-perpage"), 10) === settings.perPage);
        });
    }

    function openSettingsModal() {
        closeAllModals();
        settingsModal.classList.add("active");
        hideCommandSuggestions();
        searchInput.value = "";
    }

    function openHelpModal() {
        closeAllModals();
        helpModal.classList.add("active");
        hideCommandSuggestions();
        searchInput.value = "";
    }

    function closeAllModals() {
        detailModal.classList.remove("active");
        settingsModal.classList.remove("active");
        helpModal.classList.remove("active");
    }

    // --- RELEASES LOADER & GRID RENDERING ---

    async function loadReleases() {
        showLoader();
        try {
            let url = "";
            const limit = settings.perPage || 24;

            if (currentQuery) {
                url = `/api/search?q=${encodeURIComponent(currentQuery)}&page=${currentPage}&per_page=${limit}`;
                gridStatus.textContent = `SEARCH: "${currentQuery}"`;
            } else {
                url = `/api/latest?page=${currentPage}&per_page=${limit}`;
                gridStatus.textContent = `LATEST DISCOVERIES`;
            }

            const res = await fetch(url);
            if (!res.ok) throw new Error("Backend response error");
            const data = await res.json();

            currentItems = data.results || [];
            totalPages = data.total_pages || 1;
            currentPage = data.current_page || 1;
            resultsCount.textContent = `[${data.total_count} ITEMS]`;
            
            updatePaginationUI();
            renderGrid();
        } catch (err) {
            releasesGrid.innerHTML = `
                <div class="loader-container" style="color: var(--neon-magenta); grid-column: 1 / -1;">
                    [!] ERROR CONNECTING TO BACKEND SERVICE. RETRYING...
                </div>
            `;
            console.error(err);
        }
    }

    function renderGrid() {
        if (!currentItems || currentItems.length === 0) {
            releasesGrid.innerHTML = `
                <div class="loader-container" style="grid-column: 1 / -1;">
                    [?] NO RELEASES FOUND MATCHING QUERY.
                </div>
            `;
            return;
        }

        // Apply Pill Filter (Movies vs Series)
        let filtered = currentItems;
        if (currentFilter === "MOVIES") {
            filtered = currentItems.filter(item => !item.parsed.is_series);
        } else if (currentFilter === "SERIES") {
            filtered = currentItems.filter(item => item.parsed.is_series);
        }

        // Apply Active CLI Tag Filter (e.g. /filter 1080p, /filter hindi)
        if (activeCliFilter) {
            const f = activeCliFilter.toLowerCase();
            filtered = filtered.filter(item => {
                const qual = (item.parsed.quality || "").toLowerCase();
                const audio = (item.parsed.audio || "").toLowerCase();
                const year = (item.parsed.year || "").toString().toLowerCase();
                const title = (item.parsed.clean_title || item.raw_title || "").toLowerCase();
                return qual.includes(f) || audio.includes(f) || year.includes(f) || title.includes(f);
            });
        }

        if (filtered.length === 0) {
            releasesGrid.innerHTML = `
                <div class="loader-container" style="grid-column: 1 / -1; color: var(--neon-amber);">
                    [!] NO ITEMS MATCH ACTIVE FILTER: "${activeCliFilter}". Type <span style="color: var(--neon-cyan); cursor: pointer;" onclick="window.BhilaiApp.clearFilter()">/filter clear</span> to reset.
                </div>
            `;
            return;
        }

        releasesGrid.innerHTML = filtered.map(item => {
            const isSeries = item.parsed.is_series;
            const yearTag = item.parsed.year ? `<span class="tag tag-year">${item.parsed.year}</span>` : "";
            const qualTag = item.parsed.quality ? `<span class="tag tag-quality">${item.parsed.quality}</span>` : "";
            const typeTag = isSeries ? `<span class="tag tag-series">${item.parsed.season || 'SERIES'}</span>` : `<span class="tag">MOVIE</span>`;
            const audioTag = item.parsed.audio ? `<span class="tag">${item.parsed.audio}</span>` : "";

            return `
                <div class="release-card ${isSeries ? 'is-series' : ''}" onclick="window.BhilaiApp.openRelease(${item.id})">
                    <div>
                        <div class="card-title">${escapeHtml(item.parsed.clean_title || item.raw_title)}</div>
                        <div class="card-tags">
                            ${typeTag}
                            ${yearTag}
                            ${qualTag}
                            ${audioTag}
                        </div>
                    </div>
                    <div class="card-footer">
                        <span>#${item.id}</span>
                        <span class="card-action">[LOCKER LINKS &gt;&gt;]</span>
                    </div>
                </div>
            `;
        }).join("");
    }

    function updatePaginationUI() {
        pageIndicator.textContent = `PAGE ${currentPage} / ${totalPages}`;
        btnPrev.disabled = currentPage <= 1;
        btnNext.disabled = currentPage >= totalPages;
    }

    function showLoader() {
        releasesGrid.innerHTML = `
            <div class="loader-container" style="grid-column: 1 / -1;">
                &gt;&gt; FETCHING RELEASES FROM GATEWAY...
            </div>
        `;
    }

    async function openRelease(postId) {
        closeAllModals();
        detailModal.classList.add("active");
        modalTitle.textContent = `FETCHING RELEASE #${postId}...`;
        modalMeta.innerHTML = "";
        modalBody.innerHTML = `
            <div class="loader-container">
                &gt;&gt; PARSING LOCKER OPTIONS & QUALITY TIERS...
            </div>
        `;

        try {
            const res = await fetch(`/api/release/${postId}`);
            if (!res.ok) throw new Error("Failed to load release detail");
            const data = await res.json();

            modalTitle.textContent = data.parsed.clean_title || data.raw_title;
            modalMeta.innerHTML = `
                <div class="card-tags" style="margin-top: 6px;">
                    <span class="tag ${data.release_type === 'series' ? 'tag-series' : ''}">${data.release_type.toUpperCase()}</span>
                    ${data.parsed.year ? `<span class="tag tag-year">${data.parsed.year}</span>` : ''}
                    ${data.parsed.season ? `<span class="tag tag-series">${data.parsed.season}</span>` : ''}
                    ${data.parsed.audio ? `<span class="tag">${data.parsed.audio}</span>` : ''}
                </div>
            `;

            if (data.release_type === "series" && data.episodes && data.episodes.length > 0) {
                modalBody.innerHTML = data.episodes.map(ep => {
                    const btnHtml = ep.links.map(l => renderLockerButton(l)).join("");
                    return `
                        <div class="resolution-block">
                            <div class="resolution-header">
                                <span class="resolution-title">&gt; ${escapeHtml(ep.title)}</span>
                                <span style="font-size: 0.75rem; color: var(--text-dim);">${ep.links.length} LOCKERS</span>
                            </div>
                            <div class="button-grid">
                                ${btnHtml || '<span style="color: var(--text-muted);">No direct lockers found.</span>'}
                            </div>
                        </div>
                    `;
                }).join("");
            } else if (data.resolutions && data.resolutions.length > 0) {
                modalBody.innerHTML = data.resolutions.map(resGroup => {
                    const btnHtml = resGroup.links.map(l => renderLockerButton(l)).join("");
                    return `
                        <div class="resolution-block">
                            <div class="resolution-header">
                                <span class="resolution-title">&gt; ${escapeHtml(resGroup.quality)}</span>
                                ${resGroup.size ? `<span class="tag tag-quality">${escapeHtml(resGroup.size)}</span>` : ''}
                            </div>
                            <div class="button-grid">
                                ${btnHtml || '<span style="color: var(--text-muted);">No direct lockers found.</span>'}
                            </div>
                        </div>
                    `;
                }).join("");
            } else {
                modalBody.innerHTML = `
                    <div style="color: var(--text-muted); text-align: center; padding: 20px;">
                        No direct locker buttons found in this release.
                    </div>
                `;
            }

        } catch (err) {
            modalBody.innerHTML = `
                <div style="color: var(--neon-magenta); text-align: center; padding: 20px;">
                    [!] FAILED TO PARSE LOCKER OPTIONS FOR THIS ITEM.
                </div>
            `;
            console.error(err);
        }
    }

    function renderLockerButton(link) {
        if (link.provider.toLowerCase().includes("hubcloud")) {
            const uniqueId = `hub-btn-${Math.random().toString(36).substr(2, 9)}`;
            const isPreferred = settings.preferredServer === "server1";
            return `
                <div id="${uniqueId}" style="width: 100%;">
                    <button onclick="window.BhilaiApp.resolveDirect('${uniqueId}', '${escapeHtml(link.url)}')" class="locker-btn btn-hubcloud" style="cursor: pointer; width: 100%; ${isPreferred ? 'border-width: 2px;' : ''}">
                        <span>SERVER 1 ${isPreferred ? '★' : ''}</span>
                    </button>
                </div>
            `;
        }

        if (link.provider.toLowerCase().includes("gdflix")) {
            const gdUniqueId = `gd-btn-${Math.random().toString(36).substr(2, 9)}`;
            const isPreferred = settings.preferredServer === "server2";
            return `
                <div id="${gdUniqueId}" style="width: 100%;">
                    <button onclick="window.BhilaiApp.resolveGdflix('${gdUniqueId}', '${escapeHtml(link.url)}')" class="locker-btn btn-gdflix" style="cursor: pointer; width: 100%; ${isPreferred ? 'border-width: 2px;' : ''}">
                        <span>SERVER 2 ${isPreferred ? '★' : ''}</span>
                    </button>
                </div>
            `;
        }

        return `
            <a href="${escapeHtml(link.url)}" target="_blank" rel="noopener noreferrer" class="locker-btn btn-telegram">
                <span>${escapeHtml(link.label)}</span>
            </a>
        `;
    }

    async function resolveDirect(containerId, hubUrl) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `<div style="color: var(--neon-cyan); font-size: 0.8rem; padding: 8px; text-align: center;">&gt;&gt; CONNECTING...</div>`;

        try {
            const res = await fetch(`/api/resolve/direct?url=${encodeURIComponent(hubUrl)}`);
            if (!res.ok) throw new Error("Resolution failed");
            const data = await res.json();

            if (!data.direct_links || data.direct_links.length === 0) {
                container.innerHTML = `<div style="color: var(--neon-amber); font-size: 0.75rem; padding: 6px; text-align: center;">Link expired. <a href="${escapeHtml(hubUrl)}" target="_blank" style="color: var(--neon-cyan);">Open manually</a></div>`;
                return;
            }

            const r2Link = data.direct_links.find(dl => dl.type === "r2_direct" || dl.url.includes("r2.cloudflarestorage.com"));
            const targetLink = r2Link || data.direct_links[0];

            container.innerHTML = `
                <a href="${escapeHtml(targetLink.url)}" target="_blank" rel="noopener noreferrer" class="locker-btn btn-hubcloud" style="width: 100%; justify-content: center;">
                    <span>⬇ SERVER 1 — DOWNLOAD</span>
                </a>
            `;
        } catch (err) {
            container.innerHTML = `<div style="color: var(--neon-magenta); font-size: 0.75rem; padding: 6px; text-align: center;">[!] Failed. <a href="${escapeHtml(hubUrl)}" target="_blank" style="color: var(--neon-cyan);">Open manually</a></div>`;
            console.error(err);
        }
    }

    async function resolveGdflix(containerId, gdUrl) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `<div style="color: var(--neon-cyan); font-size: 0.8rem; padding: 8px; text-align: center;">&gt;&gt; CONNECTING...</div>`;

        try {
            const res = await fetch(`/api/resolve/gdflix?url=${encodeURIComponent(gdUrl)}`);
            if (!res.ok) throw new Error("Resolver error");
            const data = await res.json();
            const directTarget = data.direct_url || data.fastcloud_zipdisk || data.instant_10gbps || data.cloud_r2;

            if (!directTarget) {
                container.innerHTML = `<div style="color: var(--neon-amber); font-size: 0.75rem; padding: 6px; text-align: center;">Link expired. <a href="${escapeHtml(gdUrl)}" target="_blank" style="color: var(--neon-cyan);">Open manually</a></div>`;
                return;
            }

            container.innerHTML = `
                <a href="${escapeHtml(directTarget)}" target="_blank" rel="noopener noreferrer" class="locker-btn btn-gdflix" style="width: 100%; justify-content: center;">
                    <span>⬇ SERVER 2 — DOWNLOAD</span>
                </a>
            `;
        } catch (err) {
            container.innerHTML = `<div style="color: var(--neon-magenta); font-size: 0.75rem; padding: 6px; text-align: center;">[!] Failed. <a href="${escapeHtml(gdUrl)}" target="_blank" style="color: var(--neon-cyan);">Open manually</a></div>`;
            console.error(err);
        }
    }

    function showToast(msg) {
        toast.textContent = msg;
        toast.classList.add("active");
        setTimeout(() => toast.classList.remove("active"), 2200);
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Expose Global App API for inline onclick handlers
    window.BhilaiApp = {
        openRelease,
        closeModal: closeAllModals,
        showToast,
        resolveDirect,
        resolveGdflix,
        clearFilter: () => handleFilterCommand("clear"),
        selectCommand: (cmd) => {
            searchInput.value = cmd;
            executeSlashCommand(cmd);
        }
    };
})();
