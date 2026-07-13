document.addEventListener("DOMContentLoaded", () => {
    const STORAGE_KEY = "roster-hub-theme";

    // --- Theme toggle (light/dark), persisted to localStorage ---
    const themeToggle = document.querySelector("#theme-toggle");
    const root = document.documentElement;
    const storedTheme = window.localStorage.getItem(STORAGE_KEY);
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initialTheme =
        storedTheme === "dark" || storedTheme === "light"
            ? storedTheme
            : prefersDark
              ? "dark"
              : "light";

    const applyTheme = (theme, persist = true) => {
        root.dataset.theme = theme;
        if (themeToggle) {
            themeToggle.checked = theme === "dark";
            themeToggle.setAttribute("aria-checked", String(theme === "dark"));
        }
        if (persist) {
            window.localStorage.setItem(STORAGE_KEY, theme);
        }
    };

    root.dataset.density = "compact";
    applyTheme(initialTheme, false);
    themeToggle?.addEventListener("change", () => {
        applyTheme(themeToggle.checked ? "dark" : "light");
    });

    // --- Toast dismiss / auto-hide ---
    document.querySelectorAll("[data-toast]").forEach((toast) => {
        const dismiss = () => {
            toast.classList.add("is-closing");
            window.setTimeout(() => {
                toast.closest(".toast-stack")?.remove();
            }, 180);
        };
        toast.querySelector("[data-toast-close]")?.addEventListener("click", dismiss);
        window.setTimeout(dismiss, 4200);
    });

    // --- Mobile sidebar toggle ---
    const sideMenu = document.querySelector("#primary-side-menu");
    const sideMenuToggle = document.querySelector("[data-side-menu-toggle]");
    const sideMenuBackdrop = document.querySelector("[data-side-menu-backdrop]");
    const closeSideMenu = () => {
        document.body.classList.remove("side-menu-open");
        sideMenuToggle?.setAttribute("aria-expanded", "false");
    };
    const openSideMenu = () => {
        document.body.classList.add("side-menu-open");
        sideMenuToggle?.setAttribute("aria-expanded", "true");
    };
    sideMenuToggle?.addEventListener("click", () => {
        if (document.body.classList.contains("side-menu-open")) {
            closeSideMenu();
        } else {
            openSideMenu();
        }
    });
    sideMenuBackdrop?.addEventListener("click", closeSideMenu);
    sideMenu?.querySelectorAll("a, summary").forEach((element) => {
        element.addEventListener("click", () => {
            if (window.matchMedia("(max-width: 900px)").matches) {
                closeSideMenu();
            }
        });
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeSideMenu();
        }
    });
    window.addEventListener("resize", () => {
        if (!window.matchMedia("(max-width: 900px)").matches) {
            closeSideMenu();
        }
    });
});
