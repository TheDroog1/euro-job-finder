// CONFIGURAZIONE E STATO
const API_URL = 'https://www.arbeitnow.com/api/job-board-api';
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
const englishOnlyToggle = document.getElementById('english-only');
const modal = document.getElementById('job-detail-modal');
const modalBody = document.getElementById('modal-body');

// INIZIALIZZAZIONE
document.addEventListener('DOMContentLoaded', () => {
    updateDate();
    setupNavigation();
    fetchJobs();
    updateStats();
    
    // Filtri rapidi
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            const cat = chip.dataset.category;
            jobQueryInput.value = cat === 'all' ? '' : cat;
            handleSearch();
        });
    });

    // Ricerca e Filtri
    jobQueryInput.addEventListener('input', debounce(handleSearch, 500));
    countryFilter.addEventListener('change', handleSearch);
    englishOnlyToggle.addEventListener('change', handleSearch);
    
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
            
            // Aggiorna UI Tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Aggiorna Vista
            views.forEach(v => v.classList.remove('active'));
            document.getElementById(targetView).classList.add('active');
            
            // Aggiorna Titolo
            pageTitle.textContent = tab.querySelector('.tab-label').textContent;
            
            // Refresh dati se necessario
            if (targetView === 'tracker-view') renderTracker();
            if (targetView === 'saved-view') renderSaved();
        });
    });
}

// RECUPERO DATI
async function fetchJobs() {
    showLoader();
    try {
        // Carica dati reali API
        const res = await fetch(API_URL);
        const data = await res.json();
        allJobs = data.data;
        
        // Carica dati dallo Scout (se disponibili)
        try {
            const scoutRes = await fetch('data/jobs.json');
            if (scoutRes.ok) {
                const scoutJobs = await scoutRes.json();
                // Merge semplice: aggiungiamo i lavori dello scout in cima
                // Evitiamo duplicati se possibile
                const scoutSlugs = new Set(scoutJobs.map(j => j.id));
                const filteredApiJobs = allJobs.filter(j => !scoutSlugs.has(j.slug));
                
                // Trasformiamo i lavori scout nel formato dell'API per uniformità
                const formattedScout = scoutJobs.map(j => ({
                    slug: j.id,
                    title: j.title,
                    company_name: j.company,
                    location: j.location,
                    url: j.url,
                    description: "Selezionato dallo Scout 🤖",
                    tags: ["🤖 Scout Pick", j.is_junior ? "Junior" : "Tech"],
                    remote: j.location.toLowerCase().includes('remote')
                }));

                allJobs = [...formattedScout, ...filteredApiJobs];
            }
        } catch(e) { console.log("Scout data non ancora disponibile."); }

        renderJobs(allJobs);
    } catch (err) {
        jobsContainer.innerHTML = '<div class="empty-state">Errore di connessione. Riprova più tardi.</div>';
    }
}

function handleSearch() {
    const query = jobQueryInput.value.toLowerCase();
    const country = countryFilter.value.toLowerCase();
    const englishOnly = englishOnlyToggle.checked;
    const level = levelFilter.value.toLowerCase();

    let filtered = allJobs.filter(job => {
        const titleAndDesc = (job.title + job.description).toLowerCase();

        // 1. Filtro Parole Chiave / Titolo
        const matchesQuery = !query || 
            job.title.toLowerCase().includes(query) || 
            job.company_name.toLowerCase().includes(query) ||
            job.tags.some(t => t.toLowerCase().includes(query));
            
        // 2. Filtro Nazione
        const matchesCountry = !country || 
            job.location.toLowerCase().includes(country);

        // 3. Filtro Lingua (molto più severo)
        const isEnglishOrItalian = detectAllowedLanguage(job);
        const matchesLanguage = !englishOnly || isEnglishOrItalian;

        // 4. Filtro Livello (Anti-Senior rigoroso)
        let matchesLevel = true;
        if (level === 'internship' || level === 'entry') {
            const seniorTerms = ['senior', 'lead', 'manager', 'head', 'principal', 'staff', 'direttore', 'director'];
            const hasSeniorTerm = seniorTerms.some(term => job.title.toLowerCase().includes(term));
            
            const juniorTerms = ['intern', 'stage', 'entry', 'junior', 'apprendistato', 'trainee', 'graduate', 'tirocinio'];
            const hasJuniorTerm = juniorTerms.some(term => titleAndDesc.includes(term));
            
            // Se cerco junior, non deve avere termini senior nel titolo
            matchesLevel = !hasSeniorTerm && (level === '' || hasJuniorTerm || job.title.toLowerCase().includes('junior'));
        } else if (level) {
            matchesLevel = titleAndDesc.includes(level);
        }

        return matchesQuery && matchesCountry && matchesLanguage && matchesLevel;
    });

    renderJobs(filtered);
}

// RENDERING
function renderJobs(jobs) {
    if (jobs.length === 0) {
        jobsContainer.innerHTML = '<div class="empty-state">Nessun lavoro trovato.</div>';
        return;
    }

    jobsContainer.innerHTML = jobs.map(job => {
        const isSaved = savedJobs.some(s => s.slug === job.slug);
        const requirements = detectRequirements(job);
        
        return `
            <div class="ios-card" onclick="showJobDetail('${job.slug}')">
                <div class="card-header">
                    <div class="card-icon">${job.company_name.charAt(0)}</div>
                    <div class="card-title-group">
                        <div class="card-title">${job.title}</div>
                        <div class="card-subtitle">${job.company_name}</div>
                    </div>
                    <button class="save-btn ${isSaved ? 'active' : ''}" onclick="event.stopPropagation(); toggleSave('${job.slug}')">
                        ${isSaved ? '★' : '☆'}
                    </button>
                </div>
                <div class="card-tags">
                    ${requirements.map(req => `<span class="mini-tag green">${req}</span>`).join('')}
                    ${job.remote ? '<span class="mini-tag">Remote</span>' : ''}
                </div>
                <div class="card-footer">
                    <span class="card-location">📍 ${job.location}</span>
                </div>
            </div>
        `;
    }).join('');
}

function renderTracker() {
    if (applications.length === 0) {
        trackerContainer.innerHTML = '<div class="empty-state">Nessuna candidatura inviata.</div>';
        return;
    }

    trackerContainer.innerHTML = applications.map(app => `
        <div class="ios-card">
            <div class="card-header">
                <div class="card-icon">${app.company.charAt(0)}</div>
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
    const savedData = allJobs.filter(j => savedJobs.some(s => s.slug === j.slug));
    if (savedData.length === 0) {
        savedContainer.innerHTML = '<div class="empty-state">Non hai ancora salvato nulla.</div>';
        return;
    }
    
    savedContainer.innerHTML = savedData.map(job => {
        return `
            <div class="ios-card" onclick="showJobDetail('${job.slug}')">
                <div class="card-header">
                    <div class="card-icon">${job.company_name.charAt(0)}</div>
                    <div class="card-title-group">
                        <div class="card-title">${job.title}</div>
                        <div class="card-subtitle">${job.company_name}</div>
                    </div>
                    <button class="save-btn active" onclick="event.stopPropagation(); toggleSave('${job.slug}')">
                        ★
                    </button>
                </div>
                <div class="card-footer">
                    <span class="card-location">📍 ${job.location}</span>
                </div>
            </div>
        `;
    }).join('');
}

// MODAL DETTAGLI
window.showJobDetail = function(slug) {
    const job = allJobs.find(j => j.slug === slug);
    if (!job) return;

    const isSaved = savedJobs.some(s => s.slug === job.slug);
    
    modalBody.innerHTML = `
        <h2 style="font-size: 1.5rem; margin-bottom: 5px;">${job.title}</h2>
        <p style="color: var(--ios-secondary-label); margin-bottom: 20px;">${job.company_name} • ${job.location}</p>
        
        <div class="section-title-group" style="padding: 10px 0;">
            <h3 style="font-size: 1.1rem;">Requisiti Minimi</h3>
        </div>
        <div class="card-tags" style="margin-bottom: 20px;">
            ${detectRequirements(job).map(r => `<span class="mini-tag green" style="font-size: 0.8rem; padding: 6px 12px;">${r}</span>`).join('')}
        </div>

        <div style="background: #F2F2F7; padding: 15px; border-radius: 12px; margin-bottom: 20px;">
            <p style="font-size: 0.9rem; font-weight: 600; color: var(--ios-secondary-label); margin-bottom: 8px;">Descrizione Preview</p>
            <div class="job-description-preview" style="font-size: 0.9rem; color: #444; max-height: 150px; overflow-y: auto;">
                ${job.description}
            </div>
        </div>

        <div class="modal-actions">
            <button class="btn-apple-primary" onclick="applyToJob('${job.slug}')">Candidati Ora</button>
            <button class="btn-apple-secondary" onclick="toggleSave('${job.slug}'); showJobDetail('${job.slug}')">
                ${isSaved ? 'Rimuovi dai Salvati' : 'Salva Lavoro'}
            </button>
        </div>
        <button class="text-link" style="width: 100%; margin-top: 15px; text-align: center;" onclick="modal.classList.remove('active')">Chiudi</button>
    `;
    modal.classList.add('active');
};

// LOGICA CORE
window.toggleSave = function(slug) {
    const index = savedJobs.findIndex(s => s.slug === slug);
    if (index > -1) savedJobs.splice(index, 1);
    else savedJobs.push({ slug, date: new Date().toLocaleDateString() });
    
    localStorage.setItem('ej_saved', JSON.stringify(savedJobs));
    renderJobs(allJobs);
    renderSaved();
};

window.applyToJob = function(slug) {
    const job = allJobs.find(j => j.slug === slug);
    const appId = Date.now().toString();
    
    applications.push({
        id: appId,
        slug: job.slug,
        title: job.title,
        company: job.company_name,
        date: new Date().toLocaleDateString(),
        status: 'Inviata'
    });
    
    localStorage.setItem('ej_applications', JSON.stringify(applications));
    updateStats();
    modal.classList.remove('active');
    alert('Candidatura registrata nel tracker!');
    
    // Apri link originale
    window.open(job.url, '_blank');
};

window.updateAppStatus = function(id) {
    const app = applications.find(a => a.id === id);
    const stages = ['Inviata', 'Colloquio 1', 'Test Tecnico', 'Colloquio Finale', 'Offerta', 'Rifiutata'];
    const currentIdx = stages.indexOf(app.status);
    const nextIdx = (currentIdx + 1) % stages.length;
    app.status = stages[nextIdx];
    
    localStorage.setItem('ej_applications', JSON.stringify(applications));
    renderTracker();
    updateStats();
};

// UTILS
function detectRequirements(job) {
    const reqs = [];
    const text = (job.title + job.description).toLowerCase();
    
    if (text.includes('ux') || text.includes('ui') || text.includes('figma')) reqs.push('Design Focus');
    if (text.includes('react') || text.includes('vue') || text.includes('javascript')) reqs.push('JS Master');
    if (text.includes('intern') || text.includes('junior') || text.includes('stage')) reqs.push('Entry Friendly');
    if (text.includes('english')) reqs.push('English Req');
    
    return reqs.length ? reqs : ['General Tech'];
}

function detectAllowedLanguage(job) {
    const text = (job.title + job.description).toLowerCase();
    
    // Lista Nera: se contiene troppe parole di queste lingue, scartalo
    const forbiddenKeywords = [
        ' und ', ' die ', ' der ', ' das ', ' mit ', ' für ', // Tedesco
        ' est ', ' avec ', ' nelle ', ' pour ', ' une ', ' des ', // Francese
        ' och ', ' för ', ' som ' // Svedese/Altro
    ];
    
    const hasForbidden = forbiddenKeywords.filter(kw => text.includes(kw)).length > 2;
    if (hasForbidden) return false;

    // Lista Bianca: deve contenere termini EN o IT
    const allowedKeywords = [
        'english', 'proficiency', 'fluency', 'the role', 'we are looking', 'experience in',
        'italiano', 'requisiti', 'siamo alla ricerca', 'esperienza', 'responsabilità', 'candidati'
    ];
    
    return allowedKeywords.some(kw => text.includes(kw));
}

function updateStats() {
    document.getElementById('count-applied').textContent = applications.length;
    document.getElementById('count-interviews').textContent = applications.filter(a => a.status.includes('Colloquio')).length;
}

function updateDate() {
    const options = { weekday: 'long', day: 'numeric', month: 'long' };
    document.getElementById('current-date').textContent = new Date().toLocaleDateString('it-IT', options);
}

function showLoader() {
    jobsContainer.innerHTML = '<div class="empty-state">Caricamento lavori in corso...</div>';
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
