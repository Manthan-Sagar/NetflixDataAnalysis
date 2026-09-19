/**
 * Netflix Intelligence Studio — Core Frontend Application Logic
 * Interactive Visualizations, Catalog Filtering Engine, and SQL Lab
 */

(function () {
  'use strict';

  // State Management
  let appData = null;
  let chartInstances = {};
  let currentTab = 'overview';
  
  // Catalog Explorer State
  let catalogState = {
    searchQuery: '',
    typeFilter: 'ALL',
    genreFilter: 'ALL',
    countryFilter: 'ALL',
    ratingFilter: 'ALL',
    sortBy: 'year_desc',
    currentPage: 1,
    pageSize: 25,
    filteredTitles: []
  };

  // Color Constants for Charts
  const COLORS = {
    netflixRed: '#E50914',
    netflixRedHover: '#F40612',
    netflixRedAlpha: 'rgba(229, 9, 20, 0.85)',
    accentBlue: '#38BDF8',
    accentBlueAlpha: 'rgba(56, 189, 248, 0.85)',
    accentAmber: '#F59E0B',
    accentAmberAlpha: 'rgba(245, 158, 11, 0.85)',
    accentEmerald: '#10B981',
    accentEmeraldAlpha: 'rgba(16, 185, 129, 0.85)',
    accentPurple: '#A855F7',
    accentPurpleAlpha: 'rgba(168, 85, 247, 0.85)',
    accentTeal: '#2DD4BF',
    gridBorder: 'rgba(255, 255, 255, 0.06)',
    textMuted: '#94A3B8',
    cardBg: '#13141B'
  };

  // Initialize Application on DOM Ready
  document.addEventListener('DOMContentLoaded', async () => {
    await loadApplicationData();
    if (!appData) {
      console.error('Failed to load dataset.');
      return;
    }

    renderKpis();
    initTabs();
    initGlobalCharts();
    initCatalogExplorer();
    initModals();
  });

  /**
   * Load data from window.NETFLIX_DATA (bundled via data.js) or fetch data.json fallback
   */
  async function loadApplicationData() {
    if (window.NETFLIX_DATA) {
      appData = window.NETFLIX_DATA;
      return;
    }
    try {
      const response = await fetch('data.json');
      if (response.ok) {
        appData = await response.json();
      }
    } catch (e) {
      console.warn('Direct fetch failed, checking global data:', e);
    }
  }

  /**
   * Render KPI summary metrics in the top grid
   */
  function renderKpis() {
    const kpis = appData.kpis;
    if (!kpis) return;

    // Elements
    setElText('kpi-total-titles', kpis.total_titles.toLocaleString());
    setElText('kpi-movie-count', kpis.movie_count.toLocaleString());
    setElText('kpi-movie-pct', `${kpis.movie_pct}%`);
    setElText('kpi-tv-count', kpis.tv_count.toLocaleString());
    setElText('kpi-tv-pct', `${kpis.tv_pct}%`);
    setElText('kpi-avg-movie-min', `${kpis.avg_movie_min} min`);
    setElText('kpi-avg-tv-seasons', `${kpis.avg_tv_seasons} seasons`);
    setElText('kpi-mature-pct', `${kpis.mature_pct}%`);
    setElText('kpi-mature-count', `${kpis.mature_count.toLocaleString()} titles`);
    setElText('kpi-top3-pct', `${kpis.top3_concentration_pct}%`);
  }

  function setElText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  /**
   * Set up Chart.js Defaults
   */
  function configureChartJsDefaults() {
    if (typeof Chart === 'undefined') return;

    Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
    Chart.defaults.color = COLORS.textMuted;
    Chart.defaults.borderColor = COLORS.gridBorder;
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 17, 26, 0.95)';
    Chart.defaults.plugins.tooltip.titleColor = '#FFFFFF';
    Chart.defaults.plugins.tooltip.bodyColor = '#E2E8F0';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.12)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
  }

  /**
   * Initialize All Charts
   */
  function initGlobalCharts() {
    configureChartJsDefaults();

    renderCatalogCompositionChart();
    renderDurationBracketsCharts();
    renderPivotTimelineChart();
    renderTopGenresChart();
    renderRatingsChart();
    renderCountryParetoChart();
    renderSeasonalityChart();
    renderDayOfMonthChart();
    renderRegionalRadarChart();
  }

  /**
   * 1. Catalog Composition Donut Chart
   */
  function renderCatalogCompositionChart() {
    const ctx = document.getElementById('chart-composition');
    if (!ctx) return;

    const kpis = appData.kpis;
    chartInstances.composition = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Movies', 'TV Shows'],
        datasets: [{
          data: [kpis.movie_count, kpis.tv_count],
          backgroundColor: [COLORS.netflixRed, COLORS.accentBlue],
          borderColor: '#13141B',
          borderWidth: 3,
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 12, padding: 16, color: '#E2E8F0', font: { weight: 600 } }
          },
          tooltip: {
            callbacks: {
              label: (item) => {
                const val = item.raw;
                const pct = ((val / kpis.total_titles) * 100).toFixed(1);
                return ` ${item.label}: ${val.toLocaleString()} (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }

  /**
   * 2. Duration Brackets (Movie runtime brackets & TV seasons dropoff)
   */
  function renderDurationBracketsCharts() {
    const ctxMovie = document.getElementById('chart-movie-runtimes');
    const ctxTv = document.getElementById('chart-tv-seasons');
    if (!ctxMovie || !ctxTv) return;

    const dist = appData.duration_distributions;

    chartInstances.movieRuntimes = new Chart(ctxMovie, {
      type: 'bar',
      data: {
        labels: dist.movie_brackets.map(b => b.bracket),
        datasets: [{
          label: 'Movie Count',
          data: dist.movie_brackets.map(b => b.count),
          backgroundColor: COLORS.netflixRedAlpha,
          borderColor: COLORS.netflixRed,
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: COLORS.gridBorder } }
        }
      }
    });

    chartInstances.tvSeasons = new Chart(ctxTv, {
      type: 'bar',
      data: {
        labels: dist.tv_brackets.map(b => b.bracket),
        datasets: [{
          label: 'TV Show Count',
          data: dist.tv_brackets.map(b => b.count),
          backgroundColor: COLORS.accentBlueAlpha,
          borderColor: COLORS.accentBlue,
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: COLORS.gridBorder } }
        }
      }
    });
  }

  /**
   * 3. The Strategic Pivot: Vintage Release vs Netflix Ingestion Year
   */
  function renderPivotTimelineChart() {
    const ctx = document.getElementById('chart-pivot-timeline');
    if (!ctx) return;

    const data = appData.time_series_pivot;
    const labels = data.map(d => d.year);
    const released = data.map(d => d.released);
    const added = data.map(d => d.added);

    chartInstances.pivotTimeline = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Titles Added to Netflix (Catalog Ingestion)',
            data: added,
            borderColor: COLORS.netflixRed,
            backgroundColor: 'rgba(229, 9, 20, 0.18)',
            borderWidth: 3,
            tension: 0.35,
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: COLORS.netflixRed,
            pointHoverRadius: 6
          },
          {
            label: 'Titles by Release Year (Original Vintage)',
            data: released,
            borderColor: COLORS.accentAmber,
            backgroundColor: 'transparent',
            borderWidth: 2.5,
            borderDash: [5, 5],
            tension: 0.35,
            fill: false,
            pointRadius: 3,
            pointBackgroundColor: COLORS.accentAmber,
            pointHoverRadius: 5
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        plugins: {
          legend: {
            position: 'top',
            labels: { color: '#CBD5E1', font: { weight: 600 }, boxWidth: 14 }
          }
        },
        scales: {
          x: {
            grid: { display: false }
          },
          y: {
            grid: { color: COLORS.gridBorder },
            title: { display: true, text: 'Title Volume', color: COLORS.textMuted }
          }
        }
      }
    });
  }

  /**
   * 4. Top 15 Genres Stacked Bar Chart
   */
  function renderTopGenresChart() {
    const ctx = document.getElementById('chart-top-genres');
    if (!ctx) return;

    const genres = appData.top_genres;
    const labels = genres.map(g => g.genre);
    const movieCounts = genres.map(g => g.movie);
    const tvCounts = genres.map(g => g.tv);

    chartInstances.topGenres = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Movies',
            data: movieCounts,
            backgroundColor: COLORS.netflixRedAlpha,
            borderRadius: 4
          },
          {
            label: 'TV Shows',
            data: tvCounts,
            backgroundColor: COLORS.accentBlueAlpha,
            borderRadius: 4
          }
        ]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            stacked: true,
            grid: { color: COLORS.gridBorder }
          },
          y: {
            stacked: true,
            grid: { display: false }
          }
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#E2E8F0', font: { weight: 600 } }
          }
        }
      }
    });
  }

  /**
   * 5. Ratings & Maturity Breakdown
   */
  function renderRatingsChart() {
    const ctxRatings = document.getElementById('chart-ratings');
    const ctxSegments = document.getElementById('chart-maturity-segments');
    if (!ctxRatings || !ctxSegments) return;

    const ratings = appData.ratings_breakdown;
    chartInstances.ratings = new Chart(ctxRatings, {
      type: 'bar',
      data: {
        labels: ratings.map(r => r.rating),
        datasets: [
          {
            label: 'Movies',
            data: ratings.map(r => r.movie),
            backgroundColor: COLORS.netflixRedAlpha,
            borderRadius: 4
          },
          {
            label: 'TV Shows',
            data: ratings.map(r => r.tv),
            backgroundColor: COLORS.accentBlueAlpha,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: COLORS.gridBorder } }
        },
        plugins: {
          legend: { position: 'top', labels: { color: '#CBD5E1' } }
        }
      }
    });

    const segments = appData.maturity_segments;
    chartInstances.maturitySegments = new Chart(ctxSegments, {
      type: 'doughnut',
      data: {
        labels: segments.map(s => s.segment),
        datasets: [{
          data: segments.map(s => s.count),
          backgroundColor: [
            COLORS.netflixRed,
            COLORS.accentAmber,
            COLORS.accentBlue,
            COLORS.accentEmerald,
            '#64748B'
          ],
          borderColor: '#13141B',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, padding: 12, color: '#E2E8F0' } }
        }
      }
    });
  }

  /**
   * 6. Country Production Footprint & Pareto Curve
   */
  function renderCountryParetoChart() {
    const ctx = document.getElementById('chart-country-pareto');
    if (!ctx) return;

    const countries = appData.country_production.slice(0, 12);
    const labels = countries.map(c => c.country);
    const counts = countries.map(c => c.count);
    const cumPct = countries.map(c => c.cumulative_pct);

    chartInstances.countryPareto = new Chart(ctx, {
      data: {
        labels: labels,
        datasets: [
          {
            type: 'line',
            label: 'Cumulative Catalog Share (%)',
            data: cumPct,
            borderColor: COLORS.accentAmber,
            backgroundColor: 'transparent',
            borderWidth: 2.5,
            pointBackgroundColor: COLORS.accentAmber,
            pointRadius: 4,
            yAxisID: 'y1'
          },
          {
            type: 'bar',
            label: 'Titles Produced (Direct / Co-prod)',
            data: counts,
            backgroundColor: COLORS.netflixRedAlpha,
            borderRadius: 4,
            yAxisID: 'y'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: {
            position: 'left',
            grid: { color: COLORS.gridBorder },
            title: { display: true, text: 'Title Count', color: COLORS.textMuted }
          },
          y1: {
            position: 'right',
            grid: { display: false },
            min: 0,
            max: 100,
            title: { display: true, text: 'Cumulative %', color: COLORS.accentAmber },
            ticks: { callback: v => `${v}%` }
          }
        },
        plugins: {
          legend: { position: 'top', labels: { color: '#E2E8F0' } }
        }
      }
    });
  }

  /**
   * 7. Monthly Seasonality Chart
   */
  function renderSeasonalityChart() {
    const ctx = document.getElementById('chart-seasonality');
    if (!ctx) return;

    const months = appData.monthly_seasonality;
    chartInstances.seasonality = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: months.map(m => m.month),
        datasets: [
          {
            label: 'Movies Added',
            data: months.map(m => m.movies),
            backgroundColor: COLORS.netflixRedAlpha,
            borderRadius: 4
          },
          {
            label: 'TV Shows Added',
            data: months.map(m => m.tv),
            backgroundColor: COLORS.accentBlueAlpha,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { stacked: true, grid: { display: false } },
          y: { stacked: true, grid: { color: COLORS.gridBorder } }
        },
        plugins: {
          legend: { position: 'top', labels: { color: '#E2E8F0' } }
        }
      }
    });
  }

  /**
   * 8. Day of Month Ingestion Cadence
   */
  function renderDayOfMonthChart() {
    const ctx = document.getElementById('chart-day-cadence');
    if (!ctx) return;

    const days = appData.day_of_month_cadence;
    const colors = days.map(d => d.day === 1 ? COLORS.accentAmber : COLORS.netflixRedAlpha);

    chartInstances.dayCadence = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: days.map(d => `${d.day}`),
        datasets: [{
          label: 'Titles Ingested',
          data: days.map(d => d.count),
          backgroundColor: colors,
          borderRadius: 3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: COLORS.gridBorder } }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (items) => `Day ${items[0].label} of Month`,
              afterLabel: (item) => item.dataIndex === 0 ? '★ Contractual Batch Drop Spike' : ''
            }
          }
        }
      }
    });
  }

  /**
   * 9. Regional Specialization Radar Chart
   */
  function renderRegionalRadarChart() {
    const ctx = document.getElementById('chart-regional-radar');
    if (!ctx) return;

    const radar = appData.regional_radar;
    const palette = [
      { border: COLORS.netflixRed, bg: 'rgba(229, 9, 20, 0.15)' },
      { border: COLORS.accentBlue, bg: 'rgba(56, 189, 248, 0.15)' },
      { border: COLORS.accentAmber, bg: 'rgba(245, 158, 11, 0.15)' },
      { border: COLORS.accentEmerald, bg: 'rgba(16, 185, 129, 0.15)' },
      { border: COLORS.accentPurple, bg: 'rgba(168, 85, 247, 0.15)' },
      { border: COLORS.accentTeal, bg: 'rgba(45, 212, 191, 0.15)' }
    ];

    const datasets = radar.datasets.map((d, i) => {
      const p = palette[i % palette.length];
      return {
        label: d.hub,
        data: d.values,
        borderColor: p.border,
        backgroundColor: p.bg,
        borderWidth: 2,
        pointBackgroundColor: p.border,
        pointRadius: 3
      };
    });

    chartInstances.regionalRadar = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: radar.labels,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            grid: { color: COLORS.gridBorder },
            angleLines: { color: COLORS.gridBorder },
            pointLabels: { color: '#CBD5E1', font: { size: 11, weight: 600 } },
            ticks: { display: false }
          }
        },
        plugins: {
          legend: { position: 'bottom', labels: { color: '#E2E8F0', boxWidth: 12 } }
        }
      }
    });
  }

  /**
   * Tab Navigation & Chart Resize Handling
   */
  function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');
        if (targetTab === currentTab) return;

        tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        const pane = document.getElementById(`tab-${targetTab}`);
        if (pane) pane.classList.add('active');

        currentTab = targetTab;

        // Force Chart.js instances to re-render sizes
        setTimeout(() => {
          Object.values(chartInstances).forEach(inst => {
            if (inst && typeof inst.resize === 'function') {
              inst.resize();
            }
          });
        }, 50);
      });
    });

    // Global "Strategy Takeaway" Toggle triggers
    document.querySelectorAll('.btn-takeaway').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const card = e.currentTarget.closest('.visual-card');
        const drawer = card.querySelector('.takeaway-drawer');
        if (drawer) {
          drawer.classList.toggle('open');
          btn.classList.toggle('active');
        }
      });
    });

    // "Inspect SQL" Buttons
    document.querySelectorAll('.btn-sql').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const queryKey = e.currentTarget.getAttribute('data-sql-key');
        openSqlModal(queryKey);
      });
    });
  }

  /**
   * Interactive Catalog Explorer Engine
   */
  function initCatalogExplorer() {
    const searchInput = document.getElementById('catalog-search');
    const genreSelect = document.getElementById('filter-genre');
    const countrySelect = document.getElementById('filter-country');
    const ratingSelect = document.getElementById('filter-rating');
    const sortSelect = document.getElementById('filter-sort');
    const prevBtn = document.getElementById('btn-prev-page');
    const nextBtn = document.getElementById('btn-next-page');
    const exportBtn = document.getElementById('btn-export-csv');

    // Populate Dropdowns
    populateSelect(genreSelect, appData.filter_genres, 'All Genres');
    populateSelect(countrySelect, appData.filter_countries, 'All Producing Countries');
    populateSelect(ratingSelect, appData.filter_ratings, 'All Ratings');

    // Search Input with Debounce
    let debounceTimer;
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          catalogState.searchQuery = e.target.value.toLowerCase().trim();
          catalogState.currentPage = 1;
          applyCatalogFilters();
        }, 180);
      });
    }

    // Type Pills Filter
    document.querySelectorAll('.type-pill-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.type-pill-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        catalogState.typeFilter = e.currentTarget.getAttribute('data-type');
        catalogState.currentPage = 1;
        applyCatalogFilters();
      });
    });

    // Dropdown Change Listeners
    if (genreSelect) {
      genreSelect.addEventListener('change', (e) => {
        catalogState.genreFilter = e.target.value;
        catalogState.currentPage = 1;
        applyCatalogFilters();
      });
    }

    if (countrySelect) {
      countrySelect.addEventListener('change', (e) => {
        catalogState.countryFilter = e.target.value;
        catalogState.currentPage = 1;
        applyCatalogFilters();
      });
    }

    if (ratingSelect) {
      ratingSelect.addEventListener('change', (e) => {
        catalogState.ratingFilter = e.target.value;
        catalogState.currentPage = 1;
        applyCatalogFilters();
      });
    }

    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        catalogState.sortBy = e.target.value;
        applyCatalogFilters();
      });
    }

    // Pagination Listeners
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (catalogState.currentPage > 1) {
          catalogState.currentPage--;
          renderCatalogPage();
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        const maxPage = Math.ceil(catalogState.filteredTitles.length / catalogState.pageSize);
        if (catalogState.currentPage < maxPage) {
          catalogState.currentPage++;
          renderCatalogPage();
        }
      });
    }

    // Export CSV Listener
    if (exportBtn) {
      exportBtn.addEventListener('click', exportFilteredToCsv);
    }

    // Initial Filter Run
    applyCatalogFilters();
  }

  function populateSelect(selectEl, items, defaultLabel) {
    if (!selectEl || !items) return;
    selectEl.innerHTML = `<option value="ALL">${defaultLabel}</option>`;
    items.forEach(item => {
      const opt = document.createElement('option');
      opt.value = item;
      opt.textContent = item;
      selectEl.appendChild(opt);
    });
  }

  function applyCatalogFilters() {
    const raw = appData.catalog || [];
    const { searchQuery, typeFilter, genreFilter, countryFilter, ratingFilter, sortBy } = catalogState;

    const filtered = raw.filter(item => {
      // Type
      if (typeFilter !== 'ALL' && item.type !== typeFilter) return false;

      // Genre
      if (genreFilter !== 'ALL' && !item.genres.includes(genreFilter)) return false;

      // Country
      if (countryFilter !== 'ALL' && !item.country.includes(countryFilter)) return false;

      // Rating
      if (ratingFilter !== 'ALL' && item.rating !== ratingFilter) return false;

      // Search Query
      if (searchQuery) {
        const text = `${item.title} ${item.director} ${item.cast} ${item.genres} ${item.desc}`.toLowerCase();
        if (!text.includes(searchQuery)) return false;
      }

      return true;
    });

    // Sorting
    filtered.sort((a, b) => {
      if (sortBy === 'year_desc') return b.year - a.year;
      if (sortBy === 'year_asc') return a.year - b.year;
      if (sortBy === 'title_asc') return a.title.localeCompare(b.title);
      if (sortBy === 'date_added_desc') return (b.date_added || '').localeCompare(a.date_added || '');
      return 0;
    });

    catalogState.filteredTitles = filtered;
    renderCatalogPage();
  }

  function renderCatalogPage() {
    const tbody = document.getElementById('catalog-table-body');
    const countEl = document.getElementById('catalog-results-count');
    const pageInfoEl = document.getElementById('pagination-info');
    const prevBtn = document.getElementById('btn-prev-page');
    const nextBtn = document.getElementById('btn-next-page');

    if (!tbody) return;

    const total = catalogState.filteredTitles.length;
    const { currentPage, pageSize } = catalogState;
    const maxPage = Math.max(1, Math.ceil(total / pageSize));

    if (countEl) countEl.textContent = `${total.toLocaleString()} titles matching criteria`;
    if (pageInfoEl) pageInfoEl.textContent = `Page ${currentPage} of ${maxPage}`;

    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= maxPage;

    const startIdx = (currentPage - 1) * pageSize;
    const pageItems = catalogState.filteredTitles.slice(startIdx, startIdx + pageSize);

    if (pageItems.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align:center; padding: 36px; color: var(--text-muted);">
            No catalog titles matched your active filters. Try clearing search criteria.
          </td>
        </tr>
      `;
      return;
    }

    let rowsHtml = '';
    pageItems.forEach(item => {
      const isMovie = item.type === 'Movie';
      const typeBadge = isMovie
        ? `<span class="kpi-pill pill-red">Film</span>`
        : `<span class="kpi-pill pill-blue">Series</span>`;

      const ratingClass = getRatingBadgeClass(item.rating);

      rowsHtml += `
        <tr data-id="${item.id}" class="catalog-row">
          <td class="cell-title">${escapeHtml(item.title)}</td>
          <td>${typeBadge}</td>
          <td>${escapeHtml(item.year)}</td>
          <td><span class="rating-tag ${ratingClass}">${escapeHtml(item.rating || 'NR')}</span></td>
          <td>${escapeHtml(item.duration)}</td>
          <td class="cell-genres">${escapeHtml(item.genres || 'General')}</td>
        </tr>
      `;
    });

    tbody.innerHTML = rowsHtml;

    // Attach Click Handlers to open Detail Modal
    tbody.querySelectorAll('.catalog-row').forEach(tr => {
      tr.addEventListener('click', () => {
        const id = tr.getAttribute('data-id');
        openTitleDetailModal(id);
      });
    });
  }

  function getRatingBadgeClass(rating) {
    if (['TV-MA', 'R', 'NC-17'].includes(rating)) return 'rating-mature';
    if (['TV-14', 'PG-13'].includes(rating)) return 'rating-teen';
    if (['TV-Y', 'TV-Y7', 'TV-G', 'G', 'PG'].includes(rating)) return 'rating-kids';
    return '';
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /**
   * Title Detail Modal
   */
  function openTitleDetailModal(showId) {
    const item = appData.catalog.find(t => t.id === showId);
    if (!item) return;

    const modal = document.getElementById('modal-title-detail');
    if (!modal) return;

    const isMovie = item.type === 'Movie';
    setElText('modal-detail-type', isMovie ? 'Feature Film' : 'Television Series');
    setElText('modal-detail-title', item.title);
    setElText('modal-detail-year', item.year);
    setElText('modal-detail-rating', item.rating || 'Unknown');
    setElText('modal-detail-duration', item.duration);
    setElText('modal-detail-added', item.date_added ? `Added on ${item.date_added}` : 'Ingestion date unrecorded');
    setElText('modal-detail-desc', item.desc || 'No platform synopsis available.');
    setElText('modal-detail-genres', item.genres || 'Uncategorized');
    setElText('modal-detail-director', item.director || 'Uncredited / Collective');
    setElText('modal-detail-cast', item.cast || 'Undisclosed');
    setElText('modal-detail-country', item.country || 'Global');

    modal.classList.add('open');
  }

  /**
   * SQL Inspector Modal
   */
  function openSqlModal(queryKey) {
    const modal = document.getElementById('modal-sql-inspector');
    if (!modal) return;

    const insight = appData.sql_insights[queryKey];
    if (!insight) return;

    setElText('sql-modal-title', insight.title);
    setElText('sql-modal-takeaway', insight.takeaway);
    const codeEl = document.getElementById('sql-modal-code');
    if (codeEl) codeEl.textContent = insight.sql;

    modal.classList.add('open');
  }

  function initModals() {
    // Close modal on backdrop click or close button
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop || e.target.closest('.modal-close')) {
          backdrop.classList.remove('open');
        }
      });
    });

    // Close on Escape Key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-backdrop').forEach(m => m.classList.remove('open'));
      }
    });

    // Copy SQL to Clipboard
    const copyBtn = document.getElementById('btn-copy-sql');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        const code = document.getElementById('sql-modal-code').textContent;
        navigator.clipboard.writeText(code).then(() => {
          const original = copyBtn.textContent;
          copyBtn.textContent = 'Copied!';
          setTimeout(() => { copyBtn.textContent = original; }, 1500);
        });
      });
    }
  }

  /**
   * Export Filtered Catalog to CSV
   */
  function exportFilteredToCsv() {
    const items = catalogState.filteredTitles;
    if (!items || items.length === 0) {
      alert('No titles available to export.');
      return;
    }

    const headers = ['ID', 'Title', 'Type', 'Release Year', 'Rating', 'Duration', 'Country', 'Genres', 'Director', 'Date Added'];
    const rows = items.map(t => [
      `"${t.id}"`,
      `"${t.title.replace(/"/g, '""')}"`,
      `"${t.type}"`,
      t.year,
      `"${t.rating}"`,
      `"${t.duration}"`,
      `"${t.country.replace(/"/g, '""')}"`,
      `"${t.genres.replace(/"/g, '""')}"`,
      `"${t.director.replace(/"/g, '""')}"`,
      `"${t.date_added}"`
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `netflix_catalog_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

})();
