document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    
    // Refresh dashboard data every 5 minutes
    setInterval(loadDashboardData, 300000);
});

async function loadDashboardData() {
    try {
        const dashboardData = await eel.get_dashboard_stats()();
        updateDashboard(dashboardData);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function updateDashboard(data) {
    // Update summary stats
    document.getElementById('activeJobs').textContent = data.active_jobs;
    document.getElementById('newJobsToday').textContent = data.new_jobs_today;
    document.getElementById('removedJobsToday').textContent = data.removed_jobs_today;
    document.getElementById('activeCrawls').textContent = data.active_crawls;
    
    // Update jobs per website table
    const jobsTable = document.getElementById('jobsTable').getElementsByTagName('tbody')[0];
    jobsTable.innerHTML = '';
    
    if (data.jobs_per_website.length === 0) {
        const row = jobsTable.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 2;
        cell.textContent = 'Keine Daten verfügbar';
        cell.style.textAlign = 'center';
    } else {
        data.jobs_per_website.forEach(item => {
            const row = jobsTable.insertRow();
            const websiteCell = row.insertCell();
            const countCell = row.insertCell();
            
            websiteCell.textContent = item[0];
            countCell.textContent = item[1];
        });
    }
    
    // Update crawls table
    const crawlsTable = document.getElementById('crawlsTable').getElementsByTagName('tbody')[0];
    crawlsTable.innerHTML = '';
    
    if (data.recent_crawls.length === 0) {
        const row = crawlsTable.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 3;
        cell.textContent = 'Keine Daten verfügbar';
        cell.style.textAlign = 'center';
    } else {
        data.recent_crawls.forEach(item => {
            const row = crawlsTable.insertRow();
            const websiteCell = row.insertCell();
            const dateCell = row.insertCell();
            const statusCell = row.insertCell();
            
            websiteCell.textContent = item[0];
            dateCell.textContent = formatDate(item[1]);
            
            statusCell.textContent = item[2] ? 'Erfolgreich' : 'Fehlgeschlagen';
            statusCell.className = item[2] ? 'success-status' : 'error-status';
        });
    }
    
    // Load Chart.js only if it's not already loaded
    if (!window.Chart) {
        loadScript('https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js')
            .then(() => createJobTrendsChart(data.job_trends))
            .catch(error => console.error('Error loading Chart.js:', error));
    } else {
        createJobTrendsChart(data.job_trends);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('de-DE', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function loadScript(url) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = url;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

function createJobTrendsChart(trendsData) {
    console.log('Creating job trends chart with data:', trendsData);

    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded. Cannot create chart.');
        return;
    }

    // Secure destroy of existing chart
    if (window.jobTrendsChart && window.jobTrendsChart.destroy === 'function') {
        try {
            window.jobTrendsChart.destroy();
        } catch (e) {
            console.error('Error destroying existing chart:', e);
        }
    }

    // Check the canvas chart element
    const canvas = document.getElementById('jobTrendsChart');
    if (!canvas) {
        console.error('Canvas element for job trends chart not found.');
        return;
    }
    const ctx = canvas.getContext('2d');
    
    try {
        window.jobTrendsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trendsData.dates || [],
                datasets: [
                    {
                        label: 'Neue Stellen',
                        data: trendsData.new_jobs || [],
                        borderColor: 'rgb(34, 197, 94)',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'Entfernte Stellen',
                        data: trendsData.removed_jobs || [],
                        borderColor: 'rgb(239, 68, 68)',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Stellen-Entwicklung (letzte 30 Tage)'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        ticks: {
                            maxTicksLimit: 10,
                            callback: function(value, index, values) {
                                return index % 3 === 0 ? this.getLabelForValue(value) : '';
                            }
                        }
                    }
                }
            }
        });
        
        console.log('Chart erfolgreich erstellt!');
        
    } catch (error) {
        console.error('Fehler beim Erstellen des Charts:', error);
    }
}