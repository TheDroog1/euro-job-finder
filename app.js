// CONFIGURAZIONE E STATO
let allJobs = [];
let savedJobs = JSON.parse(localStorage.getItem('ej_saved')) || [];
let applications = JSON.parse(localStorage.getItem('ej_applications')) || [];

// ELEMENTI UI
const jobsContainer = document.getElementById('jobs-container');
const trackerContainer = document.getElementById('tracker-container');
const savedContainer = document.getElementById('saved-container');
const appContent = document.getElementById('app-content');
const pageTitle = document.getElementById('page-title');
const jobQueryInput = document.getElementById('job-query');
const countryFilter = document.getElementById('country-filter');

const modal = document.getElementById('job-detail-modal');
const modalBody = document.getElementById('modal-body');

// INIZIALIZZAZIONE
document.addEventListener('DOMContentLoaded', () => {
    updateDate();
    setupNavigation();
    fetchAllJobs();
    updateStats();
    
    // Filtri rapidi
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            const cat = chip.dataset.category;
            jobQueryInput.value = cat === 'all' ? '' : cat;
            applyFilters();
        });
    });

    // Ricerca e Filtri
    jobQueryInput.addEventListener('input', debounce(applyFilters, 500));
    countryFilter.addEventListener('change', applyFilters);

    
    // Chiudi modal cliccando fuori
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.remove('active');
    });
});

// NAVIGAZIONE TAB BAR
function setupNavigation() {
    const tabs = document.querySelectorAll('.tab-item');
    const views = document.querySelectorAll('.view');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetView = tab.dataset.view;
            
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            views.forEach(v => v.classList.remove('active'));
            document.getElementById(targetView).classList.add('active');
            
            pageTitle.textContent = tab.querySelector('.tab-label').textContent;
            
            if (targetView === 'tracker-view') renderTracker();
            if (targetView === 'saved-view') renderSaved();
        });
    });
}

// =============================================
// RECUPERO DATI DALLO SCOUT LOCALE
// =============================================
async function fetchAllJobs() {
    showLoader('Sincronizzazione lavori in corso...');
    
    try {
        const jobs = await fetchLocalScout();
        allJobs = jobs;

        // Deduplica per titolo+azienda
        const seen = new Set();
        allJobs = allJobs.filter(job => {
            const key = (job.title + '|' + job.company).toLowerCase();
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });

        console.log(`Totale lavori caricati: ${allJobs.length}`);
        applyFilters();
    } catch (e) {
        console.error("Errore caricamento lavori:", e);
        showLoader('Errore durante il caricamento. Riprova più tardi.');
    }
}

// DATI SCOUT LOCALI (generati da scout.py)
async function fetchLocalScout() {
    try {
        // Cache busting per avere sempre i dati più recenti
        const res = await fetch('data/jobs.json?v=' + new Date().getTime());
        if (!res.ok) return [];
        const scoutJobs = await res.json();
        return scoutJobs.map(j => {
            return {
                id: j.id || Math.random().toString(),
                title: j.title || '',
                company: j.company || '',
                location: j.location || '',
                url: j.url || '',
                description: j.description || '',
                source: j.source || '🤖 Scout',
                tags: [j.source || '🤖 Scout', j.is_junior ? 'Entry Level' : 'Tech'],
                remote: (j.location || '').toLowerCase().includes('remote')
            };
        });
    } catch (e) {
        console.log('Errore fetch locale:', e);
        return [];
    }
}

// =============================================
// FILTRI
// =============================================
function applyFilters() {
    const query = jobQueryInput.value.toLowerCase();
    const country = countryFilter.value.toLowerCase();


    let filtered = allJobs.filter(job => {
        const titleLower = (job.title || '').toLowerCase();
        const descLower = (job.description || '').toLowerCase();
        const locationLower = (job.location || '').toLowerCase();
        const companyLower = (job.company || '').toLowerCase();
        
        // 1. ESCLUSIONE SENIOR (Rigida - sul titolo)
        const seniorTerms = ['senior', 'sr.', 'lead', 'manager', 'head of', 'principal', 
                           'staff', 'director', 'architect', 'supervisor', 'vp ', 'chief'];
        if (seniorTerms.some(term => titleLower.includes(term))) return false;

        // 2. SOLO ENTRY LEVEL (titolo O descrizione)
        const juniorTerms = ['junior', 'jr', 'intern', 'stage', 'entry', 'apprendistato', 
                           'trainee', 'graduate', 'tirocinio', 'praktikum', 'associate',  
                           'volunteer', 'volontario', 'werkstudent', 'apprentice',
                           'entry-level', 'entry level', 'beginner'];
        const isEntry = juniorTerms.some(t => titleLower.includes(t)) ||
                        juniorTerms.some(t => descLower.includes(t)) ||
                        (job.tags && job.tags.some(tag => 
                            juniorTerms.some(t => (tag || '').toLowerCase().includes(t))
                        ));
        if (!isEntry) return false;

        // 4. Filtro Parole Chiave
        const matchesQuery = !query || 
            titleLower.includes(query) || 
            companyLower.includes(query) ||
            (job.tags && job.tags.some(t => (t || '').toLowerCase().includes(query)));
            
        // 5. Filtro Nazione
        const matchesCountry = !country || locationLower.includes(country);

        return matchesQuery && matchesCountry;
    });

    renderJobs(filtered);
}



// =============================================
// RENDERING
// =============================================
function renderJobs(jobs) {
    if (jobs.length === 0) {
        jobsContainer.innerHTML = '<div class="empty-state">Nessun lavoro trovato con questi filtri.</div>';
        return;
    }

    // Mostra il conteggio
    const countEl = document.getElementById('jobs-count');
    if (countEl) countEl.textContent = `${jobs.length} lavori trovati`;

    jobsContainer.innerHTML = jobs.map(job => {
        const isSaved = savedJobs.some(s => s.id === job.id);
        const requirements = detectRequirements(job);
        const safeId = (job.id || '').replace(/'/g, "\\'");
        
        return `
            <div class="ios-card" onclick="showJobDetail('${safeId}')">
                <div class="card-header">
                    <div class="card-icon" style="background:${getRandomGradient()}">${(job.company || '?').charAt(0)}</div>
                    <div class="card-title-group">
                        <div class="card-title">${job.title}</div>
                        <div class="card-subtitle">${job.company}</div>
                    </div>
                    <button class="save-btn ${isSaved ? 'active' : ''}" onclick="event.stopPropagation(); toggleSave('${safeId}')">
                        ${isSaved ? '★' : '☆'}
                    </button>
                </div>
                <div class="card-tags">
                    ${requirements.map(req => `<span class="mini-tag green">${req}</span>`).join('')}
                    ${job.remote ? '<span class="mini-tag blue">Remote</span>' : ''}
                    <span class="mini-tag purple">${job.source}</span>
                </div>
                <div class="card-footer">
                    <span class="card-location">📍 ${job.location}</span>
                </div>
            </div>
        `;
    }).join('');
}

function getRandomGradient() {
    const gradients = [
        'linear-gradient(135deg, #6366F1 0%, #A855F7 100%)',
        'linear-gradient(135deg, #3B82F6 0%, #2DD4BF 100%)',
        'linear-gradient(135deg, #F59E0B 0%, #EF4444 100%)',
        'linear-gradient(135deg, #10B981 0%, #3B82F6 100%)'
    ];
    return gradients[Math.floor(Math.random() * gradients.length)];
}

function renderTracker() {
    if (applications.length === 0) {
        trackerContainer.innerHTML = '<div class="empty-state">Nessuna candidatura inviata.</div>';
        return;
    }

    trackerContainer.innerHTML = applications.map(app => `
        <div class="ios-card">
            <div class="card-header">
                <div class="card-icon">${(app.company || '?').charAt(0)}</div>
                <div class="card-title-group">
                    <div class="card-title">${app.title}</div>
                    <div class="card-subtitle">${app.company} • ${app.status}</div>
                </div>
            </div>
            <div class="card-footer">
                <span class="card-location">Data: ${app.date}</span>
                <button class="text-link" onclick="updateAppStatus('${app.id}')">Aggiorna Step</button>
            </div>
        </div>
    `).join('');
}

function renderSaved() {
    const savedData = allJobs.filter(j => savedJobs.some(s => s.id === j.id));
    if (savedData.length === 0) {
        savedContainer.innerHTML = '<div class="empty-state">Non hai ancora salvato nulla.</div>';
        return;
    }
    
    savedContainer.innerHTML = savedData.map(job => {
        const safeId = (job.id || '').replace(/'/g, "\\'");
        return `
            <div class="ios-card" onclick="showJobDetail('${safeId}')">
                <div class="card-header">
                    <div class="card-icon" style="background:${getRandomGradient()}">${(job.company || '?').charAt(0)}</div>
                    <div class="card-title-group">
                        <div class="card-title">${job.title}</div>
                        <div class="card-subtitle">${job.company}</div>
                    </div>
                </div>
                <div class="card-footer">
                    <span class="card-location">📍 ${job.location}</span>
                </div>
            </div>
        `;
    }).join('');
}

// =============================================
// MODAL DETTAGLI
// =============================================
window.showJobDetail = function(id) {
    const job = allJobs.find(j => j.id === id);
    if (!job) return;

    const isSaved = savedJobs.some(s => s.id === job.id);
    const safeId = id.replace(/'/g, "\\'");
    
    // Pulisci la descrizione HTML
    const cleanDesc = (job.description || 'Nessuna descrizione disponibile.')
        .replace(/<[^>]*>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .substring(0, 800);
    
    modalBody.innerHTML = `
        <h2 style="font-size: 1.5rem; margin-bottom: 5px;">${job.title}</h2>
        <p style="color: var(--ios-secondary-label); margin-bottom: 20px;">${job.company} • ${job.location}</p>
        
        <div class="section-title-group" style="padding: 10px 0;">
            <h3 style="font-size: 1.1rem;">Requisiti Minimi</h3>
        </div>
        <div class="card-tags" style="margin-bottom: 20px;">
            ${detectRequirements(job).map(r => `<span class="mini-tag green" style="font-size: 0.8rem; padding: 6px 12px;">${r}</span>`).join('')}
        </div>

        <div style="background: #F2F2F7; padding: 15px; border-radius: 12px; margin-bottom: 20px;">
            <p style="font-size: 0.9rem; font-weight: 600; color: var(--ios-secondary-label); margin-bottom: 8px;">Descrizione</p>
            <div style="font-size: 0.9rem; color: #444; max-height: 200px; overflow-y: auto; line-height: 1.6;">
                ${cleanDesc}${cleanDesc.length >= 800 ? '...' : ''}
            </div>
        </div>

        <div class="modal-actions">
            <button class="btn-apple-primary" onclick="applyToJob('${safeId}')">Candidati Ora</button>
            <button class="btn-apple-secondary" onclick="toggleSave('${safeId}'); showJobDetail('${safeId}')">
                ${isSaved ? 'Rimuovi dai Salvati' : 'Salva Lavoro'}
            </button>
        </div>
        <button class="text-link" style="width: 100%; margin-top: 15px; text-align: center;" onclick="modal.classList.remove('active')">Chiudi</button>
    `;
    modal.classList.add('active');
};

// =============================================
// LOGICA CORE
// =============================================
window.toggleSave = function(id) {
    const index = savedJobs.findIndex(s => s.id === id);
    if (index > -1) savedJobs.splice(index, 1);
    else savedJobs.push({ id, date: new Date().toLocaleDateString() });
    
    localStorage.setItem('ej_saved', JSON.stringify(savedJobs));
    applyFilters();
    renderSaved();
};

window.applyToJob = function(id) {
    const job = allJobs.find(j => j.id === id);
    if (!job) return;
    
    // 1. Registra nel tracker
    const appId = Date.now().toString();
    applications.push({
        id: appId,
        jobId: job.id,
        title: job.title,
        company: job.company,
        date: new Date().toLocaleDateString(),
        status: 'Inviata'
    });
    
    localStorage.setItem('ej_applications', JSON.stringify(applications));
    updateStats();
    
    // 2. Chiudi modal e apri link SUBITO (evita blocchi popup)
    modal.classList.remove('active');
    
    if (job.url) {
        // Apri in una nuova scheda, se fallisce (es. blocco popup) chiedi all'utente
        const newWindow = window.open(job.url, '_blank');
        if (!newWindow || newWindow.closed || typeof newWindow.closed == 'undefined') {
            // Fallback per browser molto restrittivi
            window.location.href = job.url;
        }
    }
};

window.updateAppStatus = function(id) {
    const app = applications.find(a => a.id === id);
    if (!app) return;
    const stages = ['Inviata', 'Colloquio 1', 'Test Tecnico', 'Colloquio Finale', 'Offerta', 'Rifiutata'];
    const currentIdx = stages.indexOf(app.status);
    const nextIdx = (currentIdx + 1) % stages.length;
    app.status = stages[nextIdx];
    
    localStorage.setItem('ej_applications', JSON.stringify(applications));
    renderTracker();
    updateStats();
};

// =============================================
// UTILS
// =============================================
function detectRequirements(job) {
    const reqs = [];
    const text = ((job.title || '') + (job.description || '')).toLowerCase();
    
    if (text.includes('ux') || text.includes('ui') || text.includes('figma')) reqs.push('Design');
    if (text.includes('react') || text.includes('vue') || text.includes('angular') || text.includes('front')) reqs.push('Frontend');
    if (text.includes('intern') || text.includes('junior') || text.includes('stage') || text.includes('tirocinio')) reqs.push('Entry Level');
    if (text.includes('english') || text.includes('inglese')) reqs.push('English');
    if (text.includes('italiano') || text.includes('italian')) reqs.push('Italiano');
    
    return reqs.length ? reqs : ['General'];
}

function updateStats() {
    document.getElementById('count-applied').textContent = applications.length;
    document.getElementById('count-interviews').textContent = applications.filter(a => a.status.includes('Colloquio')).length;
}

function updateDate() {
    const options = { weekday: 'long', day: 'numeric', month: 'long' };
    document.getElementById('current-date').textContent = new Date().toLocaleDateString('it-IT', options);
}

function showLoader(msg) {
    jobsContainer.innerHTML = `<div class="empty-state">${msg || 'Caricamento lavori in corso...'}</div>`;
}

// RICERCA ESTERNA
window.openExternalSearch = function(platform) {
    const query = jobQueryInput.value || 'UX UI designer junior';
    const country = countryFilter.value || 'Europe';
    let url = '';

    if (platform === 'linkedin') {
        url = `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(query)}&location=${encodeURIComponent(country)}&f_E=1%2C2`;
    } else {
        url = `https://it.indeed.com/jobs?q=${encodeURIComponent(query)}&l=${encodeURIComponent(country)}&explvl=entry_level`;
    }
    window.open(url, '_blank');
};

// INSERIMENTO MANUALE
window.showManualEntry = function() {
    modalBody.innerHTML = `
        <h2 style="font-size: 1.5rem; margin-bottom: 20px;">Aggiungi Candidatura</h2>
        <div style="display: flex; flex-direction: column; gap: 15px;">
            <input type="text" id="m-company" class="ios-select" style="width:100%" placeholder="Azienda (es. Google)">
            <input type="text" id="m-title" class="ios-select" style="width:100%" placeholder="Titolo (es. UX Designer Junior)">
            <input type="text" id="m-url" class="ios-select" style="width:100%" placeholder="Link Annuncio (LinkedIn/Indeed)">
        </div>
        <button class="btn-apple-primary" onclick="saveManualEntry()">Salva nel Tracker</button>
        <button class="text-link" style="width: 100%; margin-top: 15px; text-align: center;" onclick="modal.classList.remove('active')">Annulla</button>
    `;
    modal.classList.add('active');
};

window.saveManualEntry = function() {
    const company = document.getElementById('m-company').value;
    const title = document.getElementById('m-title').value;
    const url = document.getElementById('m-url').value;

    if (!company || !title) {
        alert('Inserisci almeno Azienda e Titolo');
        return;
    }

    const appId = 'm-' + Date.now();
    applications.push({
        id: appId,
        slug: appId,
        title: title,
        company: company,
        url: url,
        date: new Date().toLocaleDateString(),
        status: 'Inviata'
    });

    localStorage.setItem('ej_applications', JSON.stringify(applications));
    updateStats();
    modal.classList.remove('active');
    alert('Candidatura manuale salvata!');
    renderTracker();
};

function debounce(func, timeout = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}
