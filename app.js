/**
 * Red White & Skewed - Story Renderer
 * v2.0 - With voting system and social sharing
 */

// ============================================
// CONFIGURATION
// ============================================

const CONFIG = {
    apiEndpoint: '/api/vote.php',
    storiesPath: '/stories/',
    siteName: 'Red, White, & Skewed',
    siteUrl: 'https://redwhiteandskewed.com'
};

// ============================================
// FINGERPRINT GENERATION
// ============================================

function generateFingerprint() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('RWS fingerprint', 2, 2);
    
    const components = [
        navigator.userAgent,
        navigator.language,
        screen.width + 'x' + screen.height,
        new Date().getTimezoneOffset(),
        canvas.toDataURL()
    ];
    
    let hash = 0;
    const str = components.join('|');
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    
    return 'fp_' + Math.abs(hash).toString(36);
}

const userFingerprint = generateFingerprint();

// Store current poll labels for results display
let currentPollLabels = {
    conservative: 'support conservative view',
    liberal: 'support liberal view'
};

// ============================================
// VOTING SYSTEM
// ============================================

async function checkVoteStatus(storyId) {
    try {
        const response = await fetch(`${CONFIG.apiEndpoint}?story_id=${encodeURIComponent(storyId)}&fingerprint=${userFingerprint}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error checking vote status:', error);
        return { success: false, error: error.message };
    }
}

async function castVote(storyId, vote) {
    try {
        const response = await fetch(CONFIG.apiEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                story_id: storyId,
                vote: vote,
                fingerprint: userFingerprint
            })
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error casting vote:', error);
        return { success: false, error: error.message };
    }
}

function updateVoteUI(storyId, userVote, results, archived) {
    const conservativeBtn = document.getElementById('vote-conservative');
    const liberalBtn = document.getElementById('vote-liberal');
    const resultsDiv = document.getElementById('vote-results');
    
    if (!conservativeBtn || !liberalBtn) return;
    
    conservativeBtn.classList.remove('selected', 'unselected');
    liberalBtn.classList.remove('selected', 'unselected');
    
    if (userVote === 'conservative') {
        conservativeBtn.classList.add('selected');
        liberalBtn.classList.add('unselected');
    } else if (userVote === 'liberal') {
        liberalBtn.classList.add('selected');
        conservativeBtn.classList.add('unselected');
    }
    
    if (archived) {
        conservativeBtn.disabled = true;
        liberalBtn.disabled = true;
        conservativeBtn.classList.add('archived');
        liberalBtn.classList.add('archived');
    }
    
    if (userVote || archived) {
        resultsDiv.innerHTML = `
            <div class="results-bar">
                <div class="results-conservative" style="width: ${results.conservative_percent}%">
                    <span>${results.conservative_percent}%</span>
                </div>
                <div class="results-liberal" style="width: ${results.liberal_percent}%">
                    <span>${results.liberal_percent}%</span>
                </div>
            </div>
            <div class="results-counts">
                <span class="count-conservative">${results.conservative.toLocaleString()} ${currentPollLabels.conservative}</span>
                <span class="count-liberal">${results.liberal.toLocaleString()} ${currentPollLabels.liberal}</span>
            </div>
            <div class="total-votes">${results.total.toLocaleString()} total votes</div>
            ${archived ? '<div class="archived-notice">Voting is closed for this story</div>' : ''}
        `;
        resultsDiv.classList.add('visible');
    }
}

async function handleVote(storyId, vote) {
    const btn = document.getElementById(`vote-${vote}`);
    btn.classList.add('loading');
    
    const result = await castVote(storyId, vote);
    
    btn.classList.remove('loading');
    
    if (result.success) {
        updateVoteUI(storyId, result.user_vote, result.results, result.archived);
    } else if (result.archived) {
        updateVoteUI(storyId, null, result.results, true);
    } else if (result.rate_limited) {
        alert('You\'re voting too fast. Please try again later.');
    } else {
        console.error('Vote error:', result.error);
    }
}

// ============================================
// SOCIAL SHARING
// ============================================

function generateShareLinks(title) {
    const url = encodeURIComponent(window.location.href);
    const shareText = encodeURIComponent(`I just read "${title}" on Red, White, & Skewed — what side are you on?`);
    const encodedTitle = encodeURIComponent(title);
    
    return {
        twitter: `https://twitter.com/intent/tweet?text=${shareText}&url=${url}`,
        facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}&quote=${shareText}`,
        linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${url}`,
        email: `mailto:?subject=${encodedTitle}&body=${shareText}%0A%0A${url}`
    };
}

function copyShareLink() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        const btn = document.querySelector('.share-copy');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
            <span>Copied!</span>
        `;
        btn.classList.add('copied');
        
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.remove('copied');
        }, 2000);
    });
}

// ============================================
// STORY RENDERING
// ============================================

function renderStory(story, storyFilename) {
    const loadingState = document.getElementById('loading-state');
    const storyContent = document.getElementById('story-content');
    
    if (!storyContent) return;
    
    // Generate story ID from filename (most reliable) or fallback to date-title combo
    let storyId;
    if (storyFilename && storyFilename !== 'latest.json') {
        // Use filename without .json extension
        storyId = storyFilename.replace('.json', '');
    } else if (story.id) {
        // Use explicit ID if provided in JSON
        storyId = story.id;
    } else {
        // Fallback: combine date and title for unique ID
        const dateSlug = (story.date || '').replace(/[^a-zA-Z0-9]/g, '-').toLowerCase();
        const titleSlug = (story.title || 'story').replace(/[^a-zA-Z0-9]/g, '-').toLowerCase().substring(0, 50);
        storyId = `${dateSlug}-${titleSlug}`.replace(/-+/g, '-').replace(/^-|-$/g, '');
    }
    
    // Format date - handle both "January 16, 2026" and "2026-01-16" formats
    let dateStr = '';
    if (story.date) {
        // Try parsing as-is first (handles "January 16, 2026" format)
        let dateObj = new Date(story.date);
        
        // If invalid, try adding time component for ISO format
        if (isNaN(dateObj.getTime())) {
            dateObj = new Date(story.date + 'T12:00:00');
        }
        
        // If still invalid, just display the raw date string
        if (isNaN(dateObj.getTime())) {
            dateStr = story.date;
        } else {
            dateStr = dateObj.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        }
    }
    
    // Generate share links
    const shareLinks = generateShareLinks(story.title || 'Today\'s Story');

    // Set dynamic poll labels for results display
    if (story.poll?.options) {
        currentPollLabels = {
            conservative: story.poll.options[0]?.label ? `chose "${story.poll.options[0].label}"` : 'support conservative view',
            liberal: story.poll.options[1]?.label ? `chose "${story.poll.options[1].label}"` : 'support liberal view'
        };
    } else {
        currentPollLabels = {
            conservative: 'support conservative view',
            liberal: 'support liberal view'
        };
    }
    
    // Build HTML
    storyContent.innerHTML = `
        <!-- Date & Headlines -->
        <div class="max-w-7xl mx-auto px-4 py-8">
            <div class="text-center mb-8">
                <time class="font-mono text-xs uppercase tracking-[0.2em] text-warm-gray">${dateStr}</time>
                <h2 class="font-display text-3xl md:text-4xl lg:text-5xl font-black text-ink mt-2 leading-tight">${story.title || 'Today\'s Story'}</h2>
                ${story.subtitle ? `<p class="text-lg text-warm-gray mt-3 max-w-2xl mx-auto">${story.subtitle}</p>` : ''}
            </div>
        </div>

        <!-- Story Hero Image -->
        ${story.image ? `
        <div class="max-w-5xl mx-auto px-4 mb-8">
            <figure class="relative">
                <img
                    src="${story.image.url}"
                    alt="${story.image.alt || story.title || 'Story image'}"
                    class="w-full h-64 md:h-[420px] object-cover shadow-lg"
                    onerror="this.closest('figure').style.display='none'"
                >
                <figcaption class="flex justify-between items-center mt-2 text-xs text-warm-gray px-1">
                    <span>${story.image.credit || ''}</span>
                    <a href="${story.image.page || '#'}" target="_blank" rel="noopener noreferrer" class="hover:text-ink hover:underline transition-colors">${story.image.source || 'Source'} ↗</a>
                </figcaption>
            </figure>
        </div>
        ` : ''}

        <!-- Two Column Layout -->
        <div class="max-w-7xl mx-auto px-4 pb-8">
            <div class="grid md:grid-cols-2 gap-0 md:gap-8 relative">
                
                <!-- VS Badge -->
                <div class="vs-badge">
                    <div class="w-14 h-14 bg-ink rounded-full flex items-center justify-center shadow-xl border-4 border-paper">
                        <span class="font-display font-black text-paper text-lg">VS</span>
                    </div>
                </div>
                
                <!-- Conservative Column -->
                <article class="story-card bg-white border-t-4 border-red-deep p-6 md:p-8 shadow-lg">
                    <div class="flex items-center gap-3 mb-4">
                        <span class="w-10 h-10 bg-red-deep/10 rounded-full flex items-center justify-center text-xl">🔴</span>
                        <div>
                            <span class="font-mono text-xs uppercase tracking-wider text-red-deep">Conservative Take</span>
                            ${story.conservative?.byline ? `<p class="text-xs text-warm-gray">${story.conservative.byline}</p>` : ''}
                        </div>
                    </div>
                    <h3 class="font-display text-2xl font-bold text-ink mb-4 leading-tight">${story.conservative?.headline || ''}</h3>
                    <div class="prose prose-sm text-gray-700 space-y-4">
                        ${formatBody(story.conservative)}
                    </div>
                    ${renderSources(story.conservative?.sources)}
                </article>
                
                <!-- Liberal Column -->
                <article class="story-card bg-white border-t-4 border-blue-deep p-6 md:p-8 shadow-lg">
                    <div class="flex items-center gap-3 mb-4">
                        <span class="w-10 h-10 bg-blue-deep/10 rounded-full flex items-center justify-center text-xl">🔵</span>
                        <div>
                            <span class="font-mono text-xs uppercase tracking-wider text-blue-deep">Liberal Take</span>
                            ${story.liberal?.byline ? `<p class="text-xs text-warm-gray">${story.liberal.byline}</p>` : ''}
                        </div>
                    </div>
                    <h3 class="font-display text-2xl font-bold text-ink mb-4 leading-tight">${story.liberal?.headline || ''}</h3>
                    <div class="prose prose-sm text-gray-700 space-y-4">
                        ${formatBody(story.liberal)}
                    </div>
                    ${renderSources(story.liberal?.sources)}
                </article>
            </div>
            
            <!-- Voting Section -->
            <div class="voting-section mt-8" id="voting-section">
                <h3 class="voting-title">${story.poll?.question || 'Which perspective resonates with you?'}</h3>
                <div class="voting-buttons">
                    <button id="vote-conservative" class="vote-btn vote-conservative" onclick="handleVote('${storyId}', 'conservative')" title="${story.poll?.options?.[0]?.description || ''}">
                        <span class="vote-icon">🔴</span>
                        <span class="vote-text">${story.poll?.options?.[0]?.label || 'I support the conservative view'}</span>
                    </button>
                    <button id="vote-liberal" class="vote-btn vote-liberal" onclick="handleVote('${storyId}', 'liberal')" title="${story.poll?.options?.[1]?.description || ''}">
                        <span class="vote-icon">🔵</span>
                        <span class="vote-text">${story.poll?.options?.[1]?.label || 'I support the liberal view'}</span>
                    </button>
                </div>
                <div id="vote-results" class="vote-results"></div>
                <div class="poll-share-section">
                    <span class="poll-share-cta">What side are your friends on?</span>
                    <div class="share-buttons-inline">
                        <a href="${shareLinks.twitter}" target="_blank" rel="noopener" class="share-icon" title="Share on X"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>
                        <a href="${shareLinks.facebook}" target="_blank" rel="noopener" class="share-icon" title="Share on Facebook"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg></a>
                        <a href="${shareLinks.linkedin}" target="_blank" rel="noopener" class="share-icon" title="Share on LinkedIn"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg></a>
                        <button class="share-icon" onclick="copyShareLink()" title="Copy Link"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg></button>
                    </div>
                </div>
            </div>
            
            <!-- Fact Check Section -->
            ${story.factcheck ? `
            <div class="mt-8 bg-gradient-to-r from-amber-50 to-yellow-50 border-l-4 border-gold p-6 md:p-8 shadow-lg">
                <div class="flex items-center gap-3 mb-4">
                    <span class="w-10 h-10 bg-gold/20 rounded-full flex items-center justify-center text-xl">⚖️</span>
                    <div>
                        <span class="font-mono text-xs uppercase tracking-wider text-gold">Fact Check & Analysis</span>
                    </div>
                </div>
                <h3 class="font-display text-2xl font-bold text-ink mb-4">${story.factcheck?.headline || 'The Facts'}</h3>
                <div class="prose prose-sm text-gray-700 space-y-4">
                    ${formatBody(story.factcheck)}
                </div>
                ${renderSources(story.factcheck?.sources)}
            </div>
            ` : ''}
            
            <!-- Social Sharing Section -->
            <div class="share-section mt-8">
                <h3 class="share-title">Share this story</h3>
                <p class="share-cta">Challenge your friends — what side are they on?</p>
                <div class="share-buttons">
                    <a href="${shareLinks.twitter}" target="_blank" rel="noopener" class="share-btn share-twitter" title="Share on X/Twitter">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                        </svg>
                        <span>Tweet</span>
                    </a>
                    <a href="${shareLinks.facebook}" target="_blank" rel="noopener" class="share-btn share-facebook" title="Share on Facebook">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                        </svg>
                        <span>Share</span>
                    </a>
                    <a href="${shareLinks.linkedin}" target="_blank" rel="noopener" class="share-btn share-linkedin" title="Share on LinkedIn">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                        </svg>
                        <span>Post</span>
                    </a>
                    <a href="${shareLinks.email}" class="share-btn share-email" title="Share via Email">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                            <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                        </svg>
                        <span>Email</span>
                    </a>
                    <button class="share-btn share-copy" onclick="copyShareLink()" title="Copy Link">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                            <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                        </svg>
                        <span>Copy</span>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Hide loading, show content
    if (loadingState) loadingState.classList.add('hidden');
    storyContent.classList.remove('hidden');

    // Update page title
    if (story.title) {
        document.title = `${story.title} | ${CONFIG.siteName}`;
    }

    // Initialize voting (pass filename to check archived status)
    initializeVoting(storyId, storyFilename);
}

function formatBody(section) {
    if (!section) return '<p>Content not available.</p>';
    
    // Handle paragraphs array (your template format)
    if (section.paragraphs && Array.isArray(section.paragraphs)) {
        return section.paragraphs.map(p => `<p>${p}</p>`).join('');
    }
    
    // Handle body as array
    if (section.body && Array.isArray(section.body)) {
        return section.body.map(p => `<p>${p}</p>`).join('');
    }
    
    // Handle body as string
    if (section.body) {
        return `<p>${section.body}</p>`;
    }
    
    // Handle if section itself is a string
    if (typeof section === 'string') {
        return `<p>${section}</p>`;
    }
    
    return '<p>Content not available.</p>';
}

function renderSources(sources) {
    if (!sources || sources.length === 0) return '';
    
    return `
        <div class="mt-6 pt-4 border-t border-gray-200">
            <p class="font-mono text-xs uppercase tracking-wider text-warm-gray mb-2">Sources</p>
            <ul class="space-y-1">
                ${sources.map(s => `
                    <li class="text-sm">
                        <a href="${s.url}" target="_blank" rel="noopener" class="text-blue-600 hover:underline">${s.text || s.name || s.title || s.url}</a>
                    </li>
                `).join('')}
            </ul>
        </div>
    `;
}

async function initializeVoting(storyId, storyFilename) {
    try {
        // Check if story is archived by looking at index.json
        let isArchivedInIndex = false;
        try {
            const indexResponse = await fetch(CONFIG.storiesPath + 'index.json');
            if (indexResponse.ok) {
                const index = await indexResponse.json();
                // Find this story in the index
                const storyEntry = index.find(s => {
                    const indexFilename = s.filename.replace('.json', '').replace('.html', '');
                    const currentFilename = (storyFilename || storyId).replace('.json', '').replace('.html', '');
                    return indexFilename === currentFilename || s.filename === storyFilename;
                });
                if (storyEntry && storyEntry.archived) {
                    isArchivedInIndex = true;
                }
            }
        } catch (e) {
            console.log('Could not check index.json for archived status');
        }
        
        const status = await checkVoteStatus(storyId);
        if (status.success) {
            // Use archived status from index.json OR from vote API
            const isArchived = isArchivedInIndex || status.archived;
            updateVoteUI(storyId, status.user_vote, status.results, isArchived);
        }
    } catch (error) {
        console.error('Error initializing voting:', error);
    }
}

// ============================================
// STORY LOADING
// ============================================

async function loadStory(storyFile) {
    try {
        const response = await fetch(CONFIG.storiesPath + storyFile);
        if (!response.ok) throw new Error('Story not found');
        const story = await response.json();
        
        // If loading latest.json, try to determine the actual filename
        let actualFilename = storyFile;
        if (storyFile === 'latest.json') {
            // Try to get filename from index.json
            try {
                const indexResponse = await fetch(CONFIG.storiesPath + 'index.json');
                if (indexResponse.ok) {
                    const index = await indexResponse.json();
                    // First non-archived story is the latest
                    const latestEntry = index.find(s => !s.archived) || index[0];
                    if (latestEntry && latestEntry.filename) {
                        actualFilename = latestEntry.filename;
                    }
                }
            } catch (e) {
                // If index.json doesn't exist, fall back to story.id or generated ID
                console.log('Could not load index.json, using fallback ID');
            }
        }
        
        renderStory(story, actualFilename);
    } catch (error) {
        console.error('Error loading story:', error);
        const loadingState = document.getElementById('loading-state');
        if (loadingState) {
            loadingState.innerHTML = `
                <div class="text-center">
                    <p class="text-red-deep font-semibold mb-2">Error loading story</p>
                    <p class="text-warm-gray text-sm">${error.message}</p>
                    <button onclick="loadStory('latest.json')" class="mt-4 px-4 py-2 bg-ink text-paper text-sm">Try Again</button>
                </div>
            `;
        }
    }
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Check URL for specific story
    const urlParams = new URLSearchParams(window.location.search);
    const storyParam = urlParams.get('story');
    
    if (storyParam) {
        loadStory(storyParam + '.json');
    } else {
        loadStory('latest.json');
    }
});

// Make functions available globally
window.handleVote = handleVote;
window.copyShareLink = copyShareLink;
window.loadStory = loadStory;
