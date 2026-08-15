/* Mestre IPTV Manager - Main JavaScript Application */

// Auto-refresh dashboard stats every 30 seconds, but only when page is visible
setInterval(function() {
    // Check if page is visible using Page Visibility API
    if (document.visibilityState === 'visible' && (window.location.pathname === '/' || window.location.pathname === '/dashboard')) {
        fetch('/api/iptv/stats')
            .then(response => response.json())
            .then(data => {
                updateDashboardStats(data);
            })
            .catch(error => console.error('Error fetching stats:', error));
    }
}, 30000);

function updateDashboardStats(stats) {
    // Update stat cards if they exist
    const statCards = document.querySelectorAll('.stat-value');
    if (statCards.length >= 9) {
        statCards[0].textContent = stats.iptvs;
        statCards[1].textContent = stats.midias;
        statCards[2].textContent = stats.filmes;
        statCards[3].textContent = stats.series;
        statCards[4].textContent = stats.tv;
        statCards[5].textContent = stats.duplicados;
        statCards[6].textContent = stats.blacklist;
        statCards[7].textContent = stats.exportados;
        statCards[8].textContent = stats.tmdb_cache;
    }
}

// Utility function to format dates
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
}

// Utility function to format duration
function formatDuration(seconds) {
    if (!seconds) return '-';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips if needed
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Load validation stats if on maintenance page
    if (window.location.pathname === '/maintenance' || window.location.pathname === '/maintenance/') {
        console.log('Loading validation stats on maintenance page...');
        loadValidationStats();
    } else {
        console.log('Not on maintenance page, skipping validation stats load');
    }
});

// TMDB Validation Functions
function validateShortNames() {
    if (!confirm('Iniciar validação TMDB de filmes com nomes curtos (≤2 palavras)?\n\nEsta operação irá:\n- Validar filmes no TMDB\n- Corrigir nomes automaticamente\n- Remover duplicatas mantendo melhor qualidade\n- Enviar não encontrados para blacklist\n\nDeseja continuar?')) {
        return;
    }

    // Show progress modal
    const progressModal = new bootstrap.Modal(document.getElementById('progressModal'));
    document.getElementById('progressTitle').textContent = 'Validando TMDB...';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressBar').textContent = '0%';
    document.getElementById('progressMessage').textContent = 'Iniciando validação...';
    progressModal.show();

    // Start validation
    fetch('/api/validation/validate-short-names', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('progressBar').style.width = '100%';
            document.getElementById('progressBar').textContent = '100%';
            document.getElementById('progressMessage').textContent = data.message;
            
            // Refresh stats after validation
            setTimeout(() => {
                loadValidationStats();
                progressModal.hide();
                alert(data.message);
            }, 2000);
        } else {
            document.getElementById('progressMessage').textContent = 'Erro: ' + data.error;
            setTimeout(() => {
                progressModal.hide();
                alert('Erro na validação: ' + data.error);
            }, 2000);
        }
    })
    .catch(error => {
        document.getElementById('progressMessage').textContent = 'Erro: ' + error;
        setTimeout(() => {
            progressModal.hide();
            alert('Erro na validação: ' + error);
        }, 2000);
    });
}

function blacklistUnvalidated() {
    if (!confirm('Enviar filmes não validados para blacklist?\n\nEsta operação irá marcar como blacklist todos os filmes que não foram encontrados no TMDB.\n\nDeseja continuar?')) {
        return;
    }

    fetch('/api/validation/blacklist-unvalidated', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            loadValidationStats();
        } else {
            alert('Erro: ' + data.error);
        }
    })
    .catch(error => {
        alert('Erro: ' + error);
    });
}

function loadValidationStats() {
    console.log('Carregando estatísticas de validação...');
    
    fetch('/api/validation/stats')
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('API response:', data);
            
            if (data.success) {
                const stats = data.stats;
                
                // Update elements with fallback for missing elements
                const totalEl = document.getElementById('moviesTotal');
                const needingEl = document.getElementById('moviesNeedingValidation');
                const validatedEl = document.getElementById('moviesValidated');
                const notFoundEl = document.getElementById('moviesNotFound');
                
                if (totalEl) {
                    totalEl.textContent = stats.movies_total || 0;
                    console.log('Updated moviesTotal:', stats.movies_total);
                } else {
                    console.error('Element moviesTotal not found');
                }
                
                if (needingEl) {
                    needingEl.textContent = stats.movies_needing_validation || 0;
                    console.log('Updated moviesNeedingValidation:', stats.movies_needing_validation);
                } else {
                    console.error('Element moviesNeedingValidation not found');
                }
                
                if (validatedEl) {
                    validatedEl.textContent = stats.movies_validated || 0;
                    console.log('Updated moviesValidated:', stats.movies_validated);
                } else {
                    console.error('Element moviesValidated not found');
                }
                
                if (notFoundEl) {
                    notFoundEl.textContent = stats.movies_not_found || 0;
                    console.log('Updated moviesNotFound:', stats.movies_not_found);
                } else {
                    console.error('Element moviesNotFound not found');
                }
                
                console.log('Validation stats loaded successfully:', stats);
            } else {
                console.error('API returned error:', data.error);
                alert('Erro ao carregar estatísticas: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading validation stats:', error);
            alert('Erro ao carregar estatísticas: ' + error);
        });
}
