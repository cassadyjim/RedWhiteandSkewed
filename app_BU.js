/**
 * Red White & Skewed - Story Renderer
 * v2.0 - With voting system and social sharing
 * 
 * Features:
 * - Loads JSON stories and renders split-view layout
 * - "I Support This View" voting buttons
 * - Social sharing with "What side are you on?" CTA
 * - Vote persistence and results display
 */

// ============================================
// CONFIGURATION
// ============================================

const CONFIG = {
    apiEndpoint: '/api/vote.php',
    storiesPath: '/stories/',
    siteName: 'Red White & Skewed',
    siteUrl: 'https://redwhiteandskewed.com'
};

// ============================================
// FINGERPRINT GENERATION (for vote tracking)
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
    
    // Simple hash
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
    
    // Update button states
    conservativeBtn.classList.remove('selected', 'unselected');
    liberalBtn.classList.remove('selected', 'unselected');
    
    if (userVote === 'conservative') {
        conservativeBtn.classList.add('selected');
        liberalBtn.classList.add('unselected');
    } else if (userVote === 'liberal') {
        liberalBtn.classList.add('selected');
        conservativeBtn.classList.add('unselected');
    }
    
    // Disable buttons if archived
    if (archived) {
        conservativeBtn.disabled = true;
        liberalBtn.disabled = true;
        conservativeBtn.classList.add('archived');
        liberalBtn.classList.add('archived');
    }
    
    // Show results if user has voted or story is archived
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
                <span class="count-conservative">${results.conservative.toLocaleString()} support conservative view</span>
                <span class="count-liberal">${results.liberal.toLocaleString()} support liberal view</span>
            </div>
            <div class="total-votes">${results.total.toLocaleString()} total votes</div>
            ${archived ? '<div class="archived-notice">Voting is closed for this story</div>' : ''}
        `;
        resultsDiv.classList.add('visible');
    }
}

// ============================================
// SOCIAL SHARING
// ============================================

function generateShareLinks(story) {
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent(story.title || 'Today\'s Story');
    const shareText = encodeURIComponent(`I just read "${story.title}" on Red White & Skewed — what side are you on?`);
    
    return {
        twitter: `https://twitter.com/intent/tweet?text=${shareText}&url=${url}`,
        facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}&quote=${shareText}`,
        linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${url}`,
        email: `mailto:?subject=${title}&body=${shareText}%0A%0A${url}`,
        copy: window.location.href
    };
}

function renderShareButtons(story) {
    const links = generateShareLinks(story);
    
    return `
        <div class="share-section">
            <h3 class="share-title">Share this story</h3>
            <p class="share-cta">Challenge your friends — what side are they on?</p>
            <div class="share-buttons">
                <a href="${links.twitter}" target="_blank" rel="noopener" class="share-btn share-twitter" title="Share on X/Twitter">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                    <span>Tweet</span>
                </a>
                <a href="${links.facebook}" target="_blank" rel="noopener" class="share-btn share-facebook" title="Share on Facebook">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                    </svg>
                    <span>Share</span>
                </a>
                <a href="${links.linkedin}" target="_blank" rel="noopener" class="share-btn share-linkedin" title="Share on LinkedIn">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                    <span>Post</span>
                </a>
                <a href="${links.email}" class="share-btn share-email" title="Share via Email">
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
    `;
}

function copyShareLink() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        const btn = document.querySelector('.share-copy');
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
            <span>Copied!</span>
        `;
        btn.classList.add('copied');
        
        setTimeout(() => {
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                    <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                </svg>
                <span>Copy</span>
            `;
            btn.classList.remove('copied');
        }, 2000);
    });
}

// ============================================
// VOTING BUTTONS RENDERER
// ============================================

function renderVotingSection(storyId) {
    return `
        <div class="voting-section" id="voting-section">
            <h3 class="voting-title">Which perspective resonates with you?</h3>
            <div class="voting-buttons">
                <button id="vote-conservative" class="vote-btn vote-conservative" onclick="handleVote('${storyId}', 'conservative')">
                    <span class="vote-icon">🔴</span>
                    <span class="vote-text">I support the conservative view</span>
                </button>
                <button id="vote-liberal" class="vote-btn vote-liberal" onclick="handleVote('${storyId}', 'liberal')">
                    <span class="vote-icon">🔵</span>
                    <span class="vote-text">I support the liberal view</span>
                </button>
            </div>
            <div id="vote-results" class="vote-results"></div>
        </div>
    `;
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
        alert('Voting is closed for this archived story.');
    } else if (result.rate_limited) {
        alert('You\'re voting too fast. Please try again later.');
    } else {
        alert(result.error || 'Error casting vote. Please try again.');
    }
}

// ============================================
// STORY RENDERING
// ============================================

function renderStory(story, storyId) {
    const container = document.getElementById('story-container');
    if (!container) return;
    
    // Format date
    const dateStr = story.date ? new Date(story.date).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }) : '';
    
    container.innerHTML = `
        <article class="story">
            <header class="story-header">
                <time class="story-date">${dateStr}</time>
                <h1 class="story-title">${story.title || 'Untitled Story'}</h1>
                ${story.subtitle ? `<p class="story-subtitle">${story.subtitle}</p>` : ''}
            </header>
            
            <div class="perspectives-container">
                <!-- Conservative Perspective -->
                <section class="perspective perspective-conservative">
                    <div class="perspective-header">
                        <span class="perspective-icon">🔴</span>
                        <h2>Conservative Take</h2>
                    </div>
                    <div class="perspective-content">
                        ${formatContent(story.conservative)}
                    </div>
                </section>
                
                <div class="vs-divider">
                    <span>VS</span>
                </div>
                
                <!-- Liberal Perspective -->
                <section class="perspective perspective-liberal">
                    <div class="perspective-header">
                        <span class="perspective-icon">🔵</span>
                        <h2>Liberal Take</h2>
                    </div>
                    <div class="perspective-content">
                        ${formatContent(story.liberal)}
                    </div>
                </section>
            </div>
            
            <!-- Voting Section -->
            ${renderVotingSection(storyId)}
            
            <!-- Fact Check Section -->
            ${story.factcheck ? `
                <section class="factcheck-section">
                    <div class="factcheck-header">
                        <span class="factcheck-icon">⚖️</span>
                        <h2>Fact Check & Analysis</h2>
                    </div>
                    <div class="factcheck-content">
                        ${formatContent(story.factcheck)}
                    </div>
                </section>
            ` : ''}
            
            <!-- Social Sharing -->
            ${renderShareButtons(story)}
        </article>
    `;
    
    // Check vote status after render
    initializeVoting(storyId);
}

function formatContent(section) {
    if (!section) return '<p>Content not available.</p>';
    
    // Handle if section is a string
    if (typeof section === 'string') {
        return `<p>${section}</p>`;
    }
    
    // Handle section with headline and body
    let html = '';
    
    if (section.headline) {
        html += `<h3 class="section-headline">${section.headline}</h3>`;
    }
    
    if (section.body) {
        // Body might be array of paragraphs or string
        if (Array.isArray(section.body)) {
            html += section.body.map(p => `<p>${p}</p>`).join('');
        } else {
            html += `<p>${section.body}</p>`;
        }
    }
    
    if (section.sources && section.sources.length > 0) {
        html += `
            <div class="sources">
                <h4>Sources:</h4>
                <ul>
                    ${section.sources.map(s => `
                        <li><a href="${s.url}" target="_blank" rel="noopener">${s.name}</a></li>
                    `).join('')}
                </ul>
            </div>
        `;
    }
    
    return html || '<p>Content not available.</p>';
}

async function initializeVoting(storyId) {
    const status = await checkVoteStatus(storyId);
    
    if (status.success) {
        updateVoteUI(storyId, status.user_vote, status.results, status.archived);
    }
}

// ============================================
// STORY LOADING
// ============================================

async function loadStory(storySlug) {
    const container = document.getElementById('story-container');
    
    // Show loading state
    if (container) {
        container.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Loading story...</p>
            </div>
        `;
    }
    
    try {
        // Determine story path
        const storyPath = storySlug === 'latest' 
            ? `${CONFIG.storiesPath}latest.json`
            : `${CONFIG.storiesPath}${storySlug}.json`;
        
        const response = await fetch(storyPath);
        
        if (!response.ok) {
            throw new Error(`Story not found: ${storySlug}`);
        }
        
        const story = await response.json();
        
        // Generate story ID from slug or date
        const storyId = storySlug !== 'latest' 
            ? storySlug 
            : (story.date || 'latest').replace(/[^a-zA-Z0-9]/g, '-');
        
        renderStory(story, storyId);
        
        // Update page title
        if (story.title) {
            document.title = `${story.title} | ${CONFIG.siteName}`;
        }
        
    } catch (error) {
        console.error('Error loading story:', error);
        
        if (container) {
            container.innerHTML = `
                <div class="error-state">
                    <h2>Error Loading Story</h2>
                    <p>Could not load story: ${storySlug}</p>
                    <button onclick="loadStory('latest')">Try Latest Story</button>
                </div>
            `;
        }
    }
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Get story from URL parameter or default to latest
    const urlParams = new URLSearchParams(window.location.search);
    const storySlug = urlParams.get('story') || 'latest';
    
    loadStory(storySlug);
});

// Make functions available globally
window.handleVote = handleVote;
window.copyShareLink = copyShareLink;
window.loadStory = loadStory;
