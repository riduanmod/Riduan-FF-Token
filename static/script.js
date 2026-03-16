let inputMethod = null;
let outputToken = null;

const step1 = document.getElementById('view-step-1');
const step2 = document.getElementById('view-step-2');
const step3 = document.getElementById('view-step-3');
const step4 = document.getElementById('view-step-4');

const grpUidPass = document.getElementById('grp-uid-pass');
const grpEat = document.getElementById('grp-eat');
const grpAccess = document.getElementById('grp-access');

function showView(viewElement) {
    document.querySelectorAll('.step-view').forEach(v => {
        v.classList.remove('active-view');
        setTimeout(() => v.style.display = 'none', 300);
    });

    setTimeout(() => {
        viewElement.style.display = 'block';
        viewElement.classList.add('active-view');
    }, 350);
}

window.selectInput = function(val) {
    inputMethod = val;

    if (val === 'access') {
        outputToken = 'jwt';
        document.getElementById('back-to-step2').setAttribute('onclick', 'goBack(1)');
        prepareStep3();
        showView(step3);
    } else {
        document.getElementById('opt-out-access').style.display = 'flex';
        showView(step2);
    }
};

window.selectOutput = function(val) {
    outputToken = val;
    document.getElementById('back-to-step2').setAttribute('onclick', 'goBack(2)');
    prepareStep3();
    showView(step3);
};

function prepareStep3() {
    grpUidPass.style.display = 'none';
    grpEat.style.display = 'none';
    grpAccess.style.display = 'none';

    if (inputMethod === 'uid_pass') grpUidPass.style.display = 'flex';
    else if (inputMethod === 'eat') grpEat.style.display = 'flex';
    else if (inputMethod === 'access') grpAccess.style.display = 'flex';

    document.getElementById('gen-error-msg').style.display = 'none';
}

window.goBack = function(stepNum) {
    if (stepNum === 1) showView(step1);
    if (stepNum === 2) showView(step2);
};

window.startOver = function() {
    inputMethod = null;
    outputToken = null;
    document.getElementById('inp-uid').value = '';
    document.getElementById('inp-pass').value = '';
    document.getElementById('inp-eat').value = '';
    document.getElementById('inp-access').value = '';
    showView(step1);
};

const genForm = document.getElementById('generate-token-form');
const genBtn = document.getElementById('gen-btn');
const errorMsg = document.getElementById('gen-error-msg');
const resultsGrid = document.getElementById('results-grid');

genForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorMsg.style.display = 'none';

    let endpoint = outputToken === 'access' ? '/api/get_access_token' : '/api/get_jwt_token';
    let queryParams = newSearchParams();

    if (inputMethod === 'uid_pass') {
        const uid = document.getElementById('inp-uid').value.trim();
        const pass = document.getElementById('inp-pass').value.trim();
        if(!uid || !pass) return showError("Please enter both UID and Password.");
        queryParams.append('uid', uid);
        queryParams.append('password', pass);
        
    } else if (inputMethod === 'eat') {
        let eatInput = document.getElementById('inp-eat').value.trim();
        if(!eatInput) return showError("Please enter EAT Token or Link.");
        
        if (eatInput.includes('eat=')) {
            try {
                const match = eatInput.match(/eat=([^&]+)/);
                if (match && match[1]) {
                    eatInput = match[1];
                }
            } catch (err) {
                console.log("Regex parsing failed", err);
            }
        }
        
        queryParams.append('eat_token', eatInput);

    } else if (inputMethod === 'access') {
        const acc = document.getElementById('inp-access').value.trim();
        if(!acc) return showError("Please enter Access Token.");
        queryParams.append('access_token', acc);
    }

    genBtn.innerHTML = '<span>Processing...</span> <i class="fa-solid fa-spinner fa-spin"></i>';
    genBtn.disabled = true;

    try {
        const response = await fetch(`${endpoint}?${queryParams.toString()}`);
        const data = await response.json();

        if (!response.ok || data.success === false) {
            throw new Error(data.error || 'Failed to generate token. (Invalid Input)');
        }

        resultsGrid.innerHTML = '';
        const keysToRender = Object.keys(data).filter(k => k !== 'success');
        
        keysToRender.forEach(key => {
            if(data[key]) resultsGrid.appendChild(createResultElement(key, data[key]));
        });

        showView(step4);

    } catch (error) {
        showError(error.message);
    } finally {
        genBtn.innerHTML = '<span>Generate Token</span> <i class="fa-solid fa-bolt-lightning"></i>';
        genBtn.disabled = false;
    }
});

function newSearchParams() {
    return new URLSearchParams();
}

function showError(msg) {
    errorMsg.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> ${msg}`;
    errorMsg.style.display = 'block';
}

function createResultElement(key, value) {
    const card = document.createElement('div');
    const isLongText = key.includes('token') || key === 'open_id';
    card.className = isLongText ? 'data-box full-span' : 'data-box';
    
    let displayLabel = key.replace('_', ' ').toUpperCase();
    let iconHtml = '<i class="fa-solid fa-code"></i>';
    
    if (key.includes('token')) {
        iconHtml = '<i class="fa-solid fa-key" style="color: var(--success);"></i>';
        displayLabel = `GENERATED ${displayLabel}`;
    }
    if (key === 'open_id') iconHtml = '<i class="fa-regular fa-id-badge" style="color: #3b82f6;"></i>';
    if (key === 'platform_type') iconHtml = '<i class="fa-solid fa-gamepad" style="color: #a855f7;"></i>';

    const safeValue = String(value).replace(/'/g, "\\'");

    card.innerHTML = `
        <div class="box-header">
            <div class="box-title">${iconHtml} <span>${displayLabel}</span></div>
            <button type="button" class="btn-copy" onclick="copyToClipboard('${safeValue}')" title="Copy">
                <i class="fa-regular fa-copy"></i>
            </button>
        </div>
        <div class="box-content">${value}</div>
    `;
    return card;
}

window.copyToClipboard = async function(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast();
    } catch (err) {
        alert('Copy failed.');
    }
};

let toastTimeout;
function showToast() {
    const toast = document.getElementById("toast");
    clearTimeout(toastTimeout);
    toast.classList.remove("show");
    setTimeout(() => {
        toast.classList.add("show");
        toastTimeout = setTimeout(() => toast.classList.remove("show"), 2000);
    }, 50);
}
