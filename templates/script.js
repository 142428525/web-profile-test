'use strict';

(function () {
    const THEME_KEY = 'web-profile-theme';

    function readTheme() {
        try {
            return localStorage.getItem(THEME_KEY);
        } catch (error) {
            return null;
        }
    }

    function saveTheme(value) {
        try {
            localStorage.setItem(THEME_KEY, value);
        } catch (error) {
            // file:// 或隐私模式下可能禁用 localStorage；主题切换仍然可用。
        }
    }

    function effectiveDark() {
        const explicit = document.body.style.colorScheme;
        if (explicit === 'dark') return true;
        if (explicit === 'light') return false;
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    function updateThemeButton() {
        const button = document.getElementById('dark-switch');
        if (!button) return;
        const dark = effectiveDark();
        button.textContent = dark ? '浅色模式' : '深色模式';
        button.setAttribute('aria-pressed', String(dark));
        button.title = dark ? '切换到浅色模式' : '切换到深色模式';
    }

    function initTheme() {
        const forced = new URLSearchParams(location.search).get('theme');
        if (forced === 'light' || forced === 'dark') {
            document.body.style.colorScheme = forced;
            saveTheme(forced);
        }

        const saved = readTheme();
        if (saved === 'dark' || saved === 'light') {
            document.body.style.colorScheme = saved;
        }

        const button = document.getElementById('dark-switch');
        if (!button) return;
        button.addEventListener('click', function () {
            const next = effectiveDark() ? 'light' : 'dark';
            document.body.style.colorScheme = next;
            saveTheme(next);
            updateThemeButton();
        });

        const media = window.matchMedia('(prefers-color-scheme: dark)');
        if (typeof media.addEventListener === 'function') {
            media.addEventListener('change', updateThemeButton);
        }
        updateThemeButton();
    }

    function initNav() {
        const here = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
        document.querySelectorAll('#menu a').forEach(function (link) {
            const href = (link.getAttribute('href') || '').toLowerCase();
            if (href === here) link.setAttribute('aria-current', 'page');
        });
    }

    function initLogFilter() {
        const input = document.getElementById('log-filter');
        if (!input) return;

        const articles = Array.from(document.querySelectorAll('#learn-log article'));
        const count = document.getElementById('log-count');

        function apply() {
            const query = input.value.trim().toLowerCase();
            let visible = 0;
            articles.forEach(function (article) {
                const match = !query || article.textContent.toLowerCase().includes(query);
                article.hidden = !match;
                if (match) visible += 1;
            });
            if (count) count.textContent = '显示 ' + visible + ' / ' + articles.length + ' 条';
        }

        input.addEventListener('input', apply);
        apply();
    }

    function initContactForm() {
        const form = document.getElementById('contact-form');
        if (!form) return;

        const status = document.getElementById('form-status');
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            if (status) status.textContent = '已收到留言（本地演示，不会上传）。';
            form.reset();
        });
    }

    function init() {
        initTheme();
        initNav();
        initLogFilter();
        initContactForm();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
