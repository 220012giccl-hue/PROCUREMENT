/**
 * Login - hardcoded credentials (frontend only, for demo)
 * Valid: admin@procurement.com / admin123
 */
(function () {
    var VALID_EMAIL = 'admin@procurement.com';
    var VALID_PASSWORD = 'admin123';
    var AUTH_KEY = 'procurement_agent_logged_in';

    function isLoggedIn() {
        return sessionStorage.getItem(AUTH_KEY) === 'true';
    }

    function setLoggedIn() {
        sessionStorage.setItem(AUTH_KEY, 'true');
    }

    function logout() {
        sessionStorage.removeItem(AUTH_KEY);
        window.location.href = 'login.html';
    }

    window.procurementLogout = logout;

    function handleSubmit(e) {
        e.preventDefault();
        var emailEl = document.getElementById('login-email');
        var passwordEl = document.getElementById('login-password');
        var errorEl = document.getElementById('login-error');
        var btnEl = document.getElementById('btn-login');

        var email = (emailEl && emailEl.value) ? emailEl.value.trim() : '';
        var password = passwordEl ? passwordEl.value : '';

        errorEl.textContent = '';

        if (!email || !password) {
            errorEl.textContent = 'Please enter email and password.';
            return;
        }

        if (email.toLowerCase() !== VALID_EMAIL || password !== VALID_PASSWORD) {
            errorEl.textContent = 'Invalid email or password.';
            if (passwordEl) passwordEl.focus();
            return;
        }

        btnEl.disabled = true;
        btnEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';
        setLoggedIn();
        window.location.href = 'index.html';
    }

    var form = document.getElementById('login-form');
    if (form) {
        form.addEventListener('submit', handleSubmit);
    }
})();
