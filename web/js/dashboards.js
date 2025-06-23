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
    
    // Update critical crawls table
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
    const ctx = document.getElementById('jobTrendsChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (window.jobTrendsChart) {
        window.jobTrendsChart.destroy();
    }
    
    window.jobTrendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trendsData.dates,
            datasets: [
                {
                    label: 'Neue Stellen',
                    data: trendsData.new_jobs,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                },
                {
                    label: 'Entfernte Stellen',
                    data: trendsData.removed_jobs,
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}