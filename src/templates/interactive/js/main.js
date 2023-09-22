'use strict';

///////////////////////////////////////////////
// GLOBAL VARIABLES

const profiles = attributeProfiles; // data from python
const correlations = correlationsData; // data from python
let attributesChart = null; // graph displayed at the attributes page
let correlationsChart = null; // graph displayed at the correlations page
let isDragging = false; // attributes scrollbar mouse dragging indicator
let chartColors = null; // color scheme for Chart.js

///////////////////////////////////////////////
// ELEMENTS

/* Header */
const heading = document.querySelector('.heading-1');
const darkmodeBtn = document.querySelector('.btn--darkmode');
const navigations = document.querySelectorAll('.nav .btn');
const summaryNav = document.querySelector('#summary');
const attributesNav = document.querySelector('#attributes');
const correlationsNav = document.querySelector('#correlations');

/* Pages */
const pages = document.querySelectorAll('.page');
const summaryPage = document.querySelector('.summary');
const attributesPage = document.querySelector('.attributes');
const correlationsPage = document.querySelector('.correlations');

/* Summary Page - Stats */
const totalAttributesStat = document.querySelector('.stats__value--attributes');
const totalRecordsStat = document.querySelector('.stats__value--records');
const totalMissStat = document.querySelector('.stats__value--miss');

/* Attributes Page - Scrollbar */
const leftArrow = document.querySelector('.scrollbar__arrow--left');
const leftArrowIcon = document.querySelector('.scrollbar__arrow--left svg');
const rightArrow = document.querySelector('.scrollbar__arrow--right');
const rightArrowIcon = document.querySelector('.scrollbar__arrow--right svg');
const chipsList = document.querySelector('.scrollbar__chips');
const attributeBtns = document.querySelectorAll('.btn--attribute');

/* Attributes Page - Statistics */
const categoriesCountStat = document.querySelector('.stats__value--categories');
const mostFrequentStat = document.querySelector('.stats__value--most');
const leastFrequentStat = document.querySelector('.stats__value--least');
const missingStat = document.querySelector('.stats__value--missing');

/* Attributes Page - Graph */
const minitableEl = document.querySelector('.minitable');
const graphTitle = document.querySelector('.box--chart .heading-2');
const attributesCanvas = document.querySelector('.canvas--attributes');

/* Attributes Page - Graph Controls */
const graphTypesBtns = document.querySelectorAll('.attributes .type .btn');
const barBtn = document.querySelector('.attributes .btn--bar');
const hbarBtn = document.querySelector('.attributes .btn--hbar');
const pieBtn = document.querySelector('.attributes .btn--pie');
const minitableBtn = document.querySelector('.attributes .btn--minitable');
const graphOptionsBtns = document.querySelectorAll('.attributes .options .btn');
const percentBtn = document.querySelector('.attributes .btn--percentage');
const logBtn = document.querySelector('.attributes .btn--log');
const donutBtn = document.querySelector('.attributes .btn--donut');
const sortBtn = document.querySelector('.attributes .btn--sort');
const reverseBtn = document.querySelector('.attributes .btn--reverse');

/* Correlations Page - Graph */
const selectOne = document.querySelector('.correlations .select--one');
const divider = document.querySelector('.correlations .divider');
const selectTwo = document.querySelector('.correlations .select--two');
const correlationsCanvas = document.querySelector('.canvas--correlations');
const matrixTitle = document.querySelector('.correlations .heading-2');

/* Correlations Page - Modal */
const helpBtn = document.querySelector('.correlations .btn--help');
const helpModal = document.querySelector('.modal');
const overlay = document.querySelector('.overlay');
const closeBtn = document.querySelector('.modal__close');

///////////////////////////////////////////////
// FUNCTIONS

// Load report page according to URL hash
function loadReport() {
  let page = window.location.hash.slice(1);

  if (!page || !['summary', 'attributes', 'correlations'].includes(page)) {
    page = 'summary';
    history.replaceState(null, null, '#' + page);
  }

  displayPage(page);
}

// Switch between report pages
function displayPage(page) {
  pages.forEach((pageEl) => pageEl.classList.remove('page--active'));
  navigations.forEach((navEl) => navEl.classList.remove('btn--active'));

  switch (page) {
    case 'summary':
      summaryPage.classList.add('page--active');
      summaryNav.classList.add('btn--active');
      break;

    case 'attributes':
      attributesPage.classList.add('page--active');
      attributesNav.classList.add('btn--active');
      updateScrollbarIcons();
      if (document.querySelectorAll('.scrollbar .btn--active').length === 0) {
        attributeBtns[0].classList.add('btn--active');
        updateStats(profiles[0]);
        attributesChart = renderGraph(attributesCanvas, attributesChart, 'bar');
      }
      break;

    case 'correlations':
      correlationsPage.classList.add('page--active');
      correlationsNav.classList.add('btn--active');
      if (correlationsChart === null) {
        correlationsChart = renderMatrix(correlationsCanvas, correlationsChart);
      }
      break;
  }
}

// Display or hide scrollbar nav arrows at the attributes page
function updateScrollbarIcons() {
  const scrollLeft = chipsList.scrollLeft;
  const max = chipsList.scrollWidth - chipsList.clientWidth - 10;
  leftArrow.classList.toggle('scrollbar__arrow--active', scrollLeft >= 10);
  rightArrow.classList.toggle('scrollbar__arrow--active', scrollLeft < max);
}

// Update stats boxes at the attributes pages
function updateStats(profile) {
  const attributeName = profile.attribute;
  const title = attributeName
    .replaceAll('_', ' ')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
  graphTitle.innerText = title;

  missingStat.innerHTML = `${(+profile.missing).toLocaleString()} <span>(${(
    (profile.missing /
      (profile.counts.reduce((a, c) => a + c, 0) + profile.missing)) *
    100
  ).toFixed(2)}%)</span>`;
  categoriesCountStat.innerText = profile.categories.length.toLocaleString();

  const maxIndex = profile.counts.indexOf(Math.max(...profile.counts));
  const minIndex = profile.counts.indexOf(Math.min(...profile.counts));

  mostFrequentStat.innerHTML = `${
    profile.categories[maxIndex]
  } <span>(${profile.percentages[maxIndex].toFixed(2)}%)</span>`;
  leastFrequentStat.innerHTML = `${
    profile.categories[minIndex]
  } <span>(${profile.percentages[minIndex].toFixed(2)}%)</span>`;
}

// Render graph according to selected attribute
function renderGraph(canvas, chart, type) {
  if (chart) chart.destroy();

  const data = profiles[canvas.dataset.attribute];

  const inputData = {
    labels: [...data.categories],
    datasets: [
      {
        label: heading.innerText,
        data: [...data.counts],
        counts: [...data.counts],
        percentages: [...data.percentages],
        backgroundColor:
          type === 'pie'
            ? chartColors.map((c) => changeTransparency(c, 0.7))
            : chartColors[canvas.dataset.attribute % chartColors.length],
      },
    ],
  };

  const config = {
    type: type === 'hbar' ? 'bar' : type,
    data: inputData,
    options: {
      scales:
        type !== 'pie'
          ? {
              x: {
                display: true,
              },
              y: {
                display: true,
              },
            }
          : {},
      indexAxis: type === 'hbar' ? 'y' : 'x',
    },
  };

  return new Chart(canvas, config);
}

// Switch between pie and donut chart
function toggleCutout(graph) {
  if (graph.options.type !== 'pie') return;
  donutBtn.classList.toggle('btn--active');
  graph.options.cutout = graph?.options?.cutout === 0 ? '50%' : 0;
  graph.update();
}

// Switch between percentage and nominal scale
function togglePercentage(graph) {
  if (!['bar', 'pie'].includes(graph.options.type)) return;

  const isPercentage = percentBtn.classList.contains('btn--active');
  percentBtn.classList.toggle('btn--active');
  const valueAxis = graph.options.indexAxis === 'x' ? 'y' : 'x';

  if (isPercentage) {
    graph.data.datasets[0].data = [...graph.data.datasets[0].counts];
    delete graph.options.plugins.tooltip.callbacks.label;
    if (graph.options.type === 'bar') {
      delete graph.options.scales[valueAxis].ticks.callback;
    }
  }

  if (!isPercentage) {
    graph.data.datasets[0].data = [...graph.data.datasets[0].percentages];
    graph.options.plugins.tooltip.callbacks.label = (context) =>
      `${context.dataset.label}: ${context.raw} %`;
    if (graph.options.type === 'bar') {
      graph.options.scales[valueAxis].ticks.callback = (value) => `${value} %`;
    }
  }

  graph.update();
}

// Switch between logarithmic and normal scale
function toggleLogScale(graph) {
  if (graph.options.type !== 'bar') return;
  logBtn.classList.toggle('btn--active');
  const valueAxis = graph.options.indexAxis === 'x' ? 'y' : 'x';
  graph.options.scales[valueAxis].type =
    graph.options.scales[valueAxis].type !== 'logarithmic'
      ? 'logarithmic'
      : 'linear';
  graph.update();
}

// Sort chart alphabeticaly
function toggleSort(graph) {
  reverseBtn.classList.remove('btn--active');

  if (!minitableEl.classList.contains('minitable--hidden')) {
    return sortMiniTable(graph.canvas);
  }

  if (sortBtn.classList.contains('btn--active')) {
    sortBtn.classList.remove('btn--active');
    const isPercentageScale = percentBtn.classList.contains('btn--active');
    const profile = profiles[graph.canvas.dataset.attribute];
    graph.config.data.labels = [...profile.categories];
    graph.config.data.datasets[0].data = isPercentageScale
      ? [...profile.percentages]
      : [...profile.counts];
    graph.config.data.datasets[0].counts = [...profile.counts];
    graph.config.data.datasets[0].percentages = [...profile.percentages];
    return graph.update();
  }

  sortBtn.classList.add('btn--active');

  const data = graph.config.data.datasets[0].data.map((data, i) => [
    graph.config.data.labels[i],
    data,
    graph.config.data.datasets[0].counts[i],
    graph.config.data.datasets[0].percentages[i],
  ]);

  const sorted = isArrayOfNumbers(data.map((v) => v[0]))
    ? data.slice().sort((a, b) => a[0] - b[0])
    : data.slice().sort((a, b) => String(a[0]).localeCompare(String(b[0])));

  graph.config.data.datasets[0].data = sorted.map((data) => data[1]);
  graph.config.data.labels = sorted.map((data) => data[0]);
  graph.config.data.datasets[0].counts = sorted.map((data) => data[2]);
  graph.config.data.datasets[0].percentages = sorted.map((data) => data[3]);

  graph.update();
}

// Sort minitable alphabeticaly
function sortMiniTable(canvas) {
  const rows = Array.from(minitableEl.querySelectorAll('.minitable__row'));

  if (sortBtn.classList.contains('btn--active')) {
    sortBtn.classList.remove('btn--active');
    const profile = profiles[canvas.dataset.attribute];
    const rows = [...profile.categories].map(
      (cat, i) =>
        `<li class='minitable__row'>
      <div class='minitable__field'>${cat}</div>
      <div class='minitable__field'>${profile.counts[i]}</div>
      <div class='minitable__field'>${profile.percentages[i]} %
        </div>
        </li>`
    );
    minitableEl.innerHTML = rows.join('\n');
    return;
  }

  const sortedRows = rows.slice().sort((rowA, rowB) => {
    const valueA = rowA.querySelector(
      '.minitable__field:first-child'
    ).textContent;
    const valueB = rowB.querySelector(
      '.minitable__field:first-child'
    ).textContent;

    if (!isNaN(valueA) && !isNaN(valueB)) {
      return parseFloat(valueA) - parseFloat(valueB);
    } else {
      return valueA.localeCompare(valueB);
    }
  });

  const sortedHtml = sortedRows.map((row) => row.outerHTML).join('');

  sortBtn.classList.add('btn--active');

  minitableEl.innerHTML = sortedHtml;
}

// Reverse chart columns (data) order
function toggleReverse(graph) {
  reverseBtn.classList.toggle('btn--active');

  if (!minitableEl.classList.contains('minitable--hidden')) {
    return reverseMinitable();
  }

  graph.config.data.datasets[0].data.reverse();
  graph.config.data.datasets[0].counts.reverse();
  graph.config.data.datasets[0].percentages.reverse();
  graph.config.data.labels.reverse();
  graph.update();
}

// Reverse rows in minitable
function reverseMinitable() {
  const rows = minitableEl.querySelectorAll('.minitable__row');
  const reversedRows = Array.from(rows)
    .reverse()
    .map((row) => row.outerHTML)
    .join('');
  minitableEl.innerHTML = reversedRows;
}

// Render correlations matrix
function renderMatrix(canvas, graph) {
  if (graph) graph.destroy();

  const styles = getComputedStyle(document.documentElement);
  const chartColor = styles.getPropertyValue('--color-two');
  const data = correlations[canvas.dataset.correlations];
  const maxCorrelation = Math.max(...data.map((corr) => corr.v));
  const attributeOne = selectOne.value;
  const attributeTwo = selectTwo.value;

  const labelsX =
    attributeOne === 'Overall Correlations'
      ? profiles.map((p) => p.attribute)
      : profiles.find((p) => p.attribute === attributeOne).categories;

  const labelsY =
    attributeOne === 'Overall Correlations'
      ? profiles.map((p) => p.attribute)
      : profiles.find((p) => p.attribute === attributeTwo).categories;

  const sortedLabelsX = isArrayOfNumbers(labelsX)
    ? labelsX.slice().sort((a, b) => a - b)
    : labelsX.slice().sort((a, b) => String(a).localeCompare(String(b)));

  const sortedLabelsY = isArrayOfNumbers(labelsY)
    ? labelsY.slice().sort((a, b) => a - b)
    : labelsY.slice().sort((a, b) => String(a).localeCompare(String(b)));

  const inputData = {
    datasets: [
      {
        label: heading.innerText,
        data: data,
        backgroundColor: (context) => {
          const transparency =
            context.dataset.data[context.dataIndex].v / maxCorrelation;
          return changeTransparency(chartColor, transparency);
        },
        width(context) {
          const a = context.chart.chartArea;
          if (!a) return 0;
          return (a.right - a.left) / labelsX.length - 2;
        },
        height(context) {
          const a = context.chart.chartArea;
          if (!a) return 0;
          return (a.bottom - a.top) / labelsY.length - 2;
        },
      },
    ],
  };

  const config = {
    type: 'matrix',
    data: inputData,
    options: {
      layout: {
        padding: {
          right: 60,
        },
      },
      scales: {
        x: {
          type: 'category',
          labels: sortedLabelsX,
          ticks: {
            display: true,
            autoSkip: false,
          },
          grid: {
            display: false,
          },
          border: {
            display: false,
          },
        },
        y: {
          type: 'category',
          labels: sortedLabelsY,
          offset: true,
          reverse: false,
          ticks: {
            display: true,
            autoSkip: false,
          },
          grid: {
            display: false,
          },
          border: {
            display: false,
          },
        },
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: (context) => {
              const data = context.dataset.data[context.dataIndex];
              return `${data.x} x ${data.y}: ${data.v}`;
            },
            title: () => `${matrixTitle.innerText}`,
          },
        },
      },
    },
    plugins: [colorScaleLegend(0, maxCorrelation, chartColor)],
  };

  return new Chart(canvas, config);
}

// ColorScaleLegend plugin for correlation matrix
function colorScaleLegend(min, max, chartColor) {
  return {
    id: 'colorScaleLegend',
    afterDatasetsDraw(chart) {
      const {
        ctx,
        chartArea: { top, bottom, height, right },
        config: {
          options: { layout },
        },
      } = chart;

      const gradient = ctx.createLinearGradient(0, top, 0, height);
      gradient.addColorStop(0, changeTransparency(chartColor, 1));
      gradient.addColorStop(1, changeTransparency(chartColor, 0));

      ctx.fillStyle = gradient;
      ctx.fillRect(right + layout.padding.right - 30, top, 15, height);

      const styles = getComputedStyle(document.documentElement);

      ctx.font = '12px Poppins';
      ctx.textAlign = 'center';
      ctx.fillStyle = styles.getPropertyValue('--color-grey-700'); // TODO fix

      ctx.fillText(
        selectOne.value === 'Overall Correlations' ? min.toFixed(2) : min,
        right + layout.padding.right - 22.5,
        bottom + 12
      );

      ctx.fillText(
        selectOne.value === 'Overall Correlations' ? max.toFixed(2) : max,
        right + layout.padding.right - 22.5,
        top - 10
      );
    },
  };
}

// Open modal window with help for correlations
function openModal() {
  helpModal.classList.remove('modal--hidden');
  overlay.classList.remove('overlay--hidden');
}

// Close modal window with help for correlations
function closeModal() {
  helpModal.classList.add('modal--hidden');
  overlay.classList.add('overlay--hidden');
}

// Update chart.js config for darkmode or lightmode
function updateChartJsConfig() {
  const styles = getComputedStyle(document.documentElement);

  Chart.defaults.font.family = 'Poppins'; // font family
  Chart.defaults.font.weight = 500; // font weight
  Chart.defaults.color = styles.getPropertyValue('--color-grey-700'); // font color
  Chart.defaults.scale.border.color =
    styles.getPropertyValue('--color-grey-300'); // axis color
  Chart.defaults.borderColor = styles.getPropertyValue('--color-grey-200'); // border color
  Chart.defaults.elements.arc.borderColor =
    styles.getPropertyValue('--color-grey-0'); //pie chart border color

  chartColors = [
    styles.getPropertyValue('--color-one'),
    styles.getPropertyValue('--color-two'),
    styles.getPropertyValue('--color-three'),
    styles.getPropertyValue('--color-four'),
    styles.getPropertyValue('--color-five'),
    styles.getPropertyValue('--color-six'),
    styles.getPropertyValue('--color-seven'),
    styles.getPropertyValue('--color-eight'),
    styles.getPropertyValue('--color-nine'),
    styles.getPropertyValue('--color-ten'),
    styles.getPropertyValue('--color-eleven'),
    styles.getPropertyValue('--color-twelve'),
    styles.getPropertyValue('--color-thirteen'),
    styles.getPropertyValue('--color-fourteen'),
  ];
}

// Update chart colors for lightmode or darkmode
function updateChartColors(chart) {
  if (!chart) return;

  const chartType = chart?.config?.type;
  const styles = getComputedStyle(document.documentElement);

  if (['bar', 'matrix'].includes(chartType)) {
    chart.options.scales.x.grid.color =
      styles.getPropertyValue('--color-grey-200');
    chart.options.scales.y.grid.color =
      styles.getPropertyValue('--color-grey-200');
    chart.options.scales.x.border.color =
      styles.getPropertyValue('--color-grey-300');
    chart.options.scales.y.border.color =
      styles.getPropertyValue('--color-grey-300');
    chart.options.scales.x.ticks.color =
      styles.getPropertyValue('--color-grey-700');
    chart.options.scales.y.ticks.color =
      styles.getPropertyValue('--color-grey-700');
  }

  if (chartType === 'matrix') {
    const maxCorrelation = Math.max(
      ...chart.data.datasets[0].data.map((corr) => corr.v)
    );

    const styles = getComputedStyle(document.documentElement);
    const chartColor = styles.getPropertyValue('--color-two');

    chart.data.datasets[0].backgroundColor = (context) => {
      const transparency =
        context.dataset.data[context.dataIndex].v / maxCorrelation;
      return changeTransparency(chartColor, transparency);
    };

    chart.config.plugins[0] = colorScaleLegend(0, maxCorrelation, chartColor);
  }

  if (chartType === 'pie') {
    chart.options.borderColor = styles.getPropertyValue('--color-grey-0');
  }

  chart.options.plugins.legend.labels.color =
    styles.getPropertyValue('--color-grey-700');

  if (chartType === 'bar') {
    chart.config.data.datasets[0].backgroundColor =
      chartColors[attributesCanvas.dataset.attribute % chartColors.length];
  }

  if (chartType === 'pie') {
    chart.config.data.datasets[0].backgroundColor =
      chart.config.data.datasets[0].backgroundColor.map((_, i) =>
        changeTransparency(chartColors[i], 0.7)
      );
  }

  chart.update();
}

/* Change transparency of HEX color */
function changeTransparency(hexColor, transparency) {
  hexColor = hexColor.replace(/^#/, '');
  transparency = Math.min(1, Math.max(0, transparency));
  const alpha = Math.round(transparency * 255);
  const alphaHex = alpha.toString(16).padStart(2, '0');
  const r = parseInt(hexColor.slice(0, 2), 16);
  const g = parseInt(hexColor.slice(2, 4), 16);
  const b = parseInt(hexColor.slice(4, 6), 16);
  const updatedHexColor = `#${((1 << 24) | (r << 16) | (g << 8) | b)
    .toString(16)
    .slice(1)}${alphaHex}`;
  return updatedHexColor;
}

/* Format summary stats according to localization */
function formatSummaryStats() {
  totalAttributesStat.innerText =
    (+totalAttributesStat.innerText).toLocaleString();
  totalRecordsStat.innerText = (+totalRecordsStat.innerText).toLocaleString();
  totalMissStat.innerHTML = `${(+totalMissStat.innerText
    .split('(')[0]
    .trim()).toLocaleString()} <span>(${
    totalMissStat.innerText.split('(')[1]
  }</span>`;
}

// Render bar chart at attributes page
function handleBarBtn() {
  minitableEl.classList.add('minitable--hidden');
  attributesChart = renderGraph(attributesCanvas, attributesChart, 'bar');
  graphOptionsBtns.forEach((btn) => btn.classList.remove('btn--active'));
  graphTypesBtns.forEach((btn) => btn.classList.remove('btn--active'));
  barBtn.classList.add('btn--active');
  percentBtn.classList.remove('btn--hidden');
  logBtn.classList.remove('btn--hidden');
  donutBtn.classList.add('btn--hidden');
}

// Render horizontal bar chart
function handleHbarBtn() {
  minitableEl.classList.add('minitable--hidden');
  attributesChart = renderGraph(attributesCanvas, attributesChart, 'hbar');
  graphOptionsBtns.forEach((btn) => btn.classList.remove('btn--active'));
  graphTypesBtns.forEach((btn) => btn.classList.remove('btn--active'));
  hbarBtn.classList.add('btn--active');
  percentBtn.classList.remove('btn--hidden');
  logBtn.classList.remove('btn--hidden');
  donutBtn.classList.add('btn--hidden');
}

// Render pie chart at attributes page
function handlePieBtn() {
  minitableEl.classList.add('minitable--hidden');
  attributesChart = renderGraph(attributesCanvas, attributesChart, 'pie');
  graphOptionsBtns.forEach((btn) => btn.classList.remove('btn--active'));
  graphTypesBtns.forEach((btn) => btn.classList.remove('btn--active'));
  pieBtn.classList.add('btn--active');
  donutBtn.classList.remove('btn--hidden');
  percentBtn.classList.remove('btn--hidden');
  logBtn.classList.add('btn--hidden');
}

// Render minitable at attributes page
function handleMinitableBtn() {
  graphTypesBtns.forEach((btn) => btn.classList.remove('btn--active'));
  minitableBtn.classList.add('btn--active');
  graphOptionsBtns.forEach((btn) => btn.classList.remove('btn--active'));
  percentBtn.classList.add('btn--hidden');
  logBtn.classList.add('btn--hidden');
  donutBtn.classList.add('btn--hidden');
  attributesChart.destroy();
  attributesCanvas.classList.add('canvas--hidden');
  const profile = profiles[attributesCanvas.dataset.attribute];
  const rows = profile.categories.map(
    (cat, i) =>
      `<li class='minitable__row'>
    <div class='minitable__field'>${cat}</div>
    <div class='minitable__field'>${profile.counts[i]}</div>
    <div class='minitable__field'>${profile.percentages[i]} %
      </div>
      </li>`
  );
  minitableEl.innerHTML = rows.join('\n');
  minitableEl.classList.remove('minitable--hidden');
}

// Switch profiled attribute at attributes page
function handleAttributesBtns(btn, i) {
  btn.addEventListener('click', () => {
    attributeBtns.forEach((btn) => btn.classList.remove('btn--active'));
    btn.classList.add('btn--active');
    graphTypesBtns.forEach((btn) => btn.classList.remove('btn--active'));
    barBtn.classList.add('btn--active');
    graphOptionsBtns.forEach((btn) => btn.classList.remove('btn--active'));
    percentBtn.classList.remove('btn--hidden');
    logBtn.classList.remove('btn--hidden');
    donutBtn.classList.add('btn--hidden');
    updateStats(profiles[i]);
    minitableEl.classList.add('minitable--hidden');
    attributesCanvas.setAttribute('data-attribute', i);
    attributesChart = renderGraph(attributesCanvas, attributesChart, 'bar');
  });
}

// Handle first attribute select at correlation page
function handleSelectOne() {
  const individualCorrelations = selectOne.value !== 'Overall Correlations';
  selectTwo.classList.toggle('select--hidden', !individualCorrelations);
  divider.classList.toggle('divider--hidden', !individualCorrelations);

  const newValue = individualCorrelations
    ? `${selectOne.value} x ${selectTwo.value}`
    : 'Overall Correlations';

  matrixTitle.innerText = newValue;
  correlationsCanvas.setAttribute('data-correlations', newValue);
  correlationsChart = renderMatrix(correlationsCanvas, correlationsChart);
}

// Handle second attribute select at correlation page
function handleSelectTwo() {
  const individualCorrelations = selectOne.value !== 'Overall Correlations';

  const newValue = individualCorrelations
    ? `${selectOne.value} x ${selectTwo.value}`
    : 'Overall Correlations';

  matrixTitle.innerText = newValue;
  correlationsCanvas.setAttribute('data-correlations', newValue);
  correlationsChart = renderMatrix(correlationsCanvas, correlationsChart);
}

// Handle darkmode toggle
function handleDarkmodeBtn() {
  const sunIcon = `
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
  </svg>`;

  const moonIcon = `
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
  </svg>`;

  const isLightMode = document.documentElement.classList.contains('light-mode');

  if (isLightMode) {
    document.documentElement.classList.add('dark-mode');
    document.documentElement.classList.remove('light-mode');
    darkmodeBtn.innerHTML = sunIcon;
  } else {
    document.documentElement.classList.add('light-mode');
    document.documentElement.classList.remove('dark-mode');
    darkmodeBtn.innerHTML = moonIcon;
  }

  updateChartJsConfig();
  updateChartColors(attributesChart);
  updateChartColors(correlationsChart);
}

///////////////////////////////////////////////
// EVENT HANDLERS

/* Page Navigation */
summaryNav.addEventListener('click', () => displayPage('summary'));
attributesNav.addEventListener('click', () => displayPage('attributes'));
correlationsNav.addEventListener('click', () => displayPage('correlations'));

/* Graph Types Buttons */
barBtn.addEventListener('click', () => handleBarBtn());
hbarBtn.addEventListener('click', () => handleHbarBtn());
pieBtn.addEventListener('click', () => handlePieBtn());
minitableBtn.addEventListener('click', () => handleMinitableBtn());

/* Graph Options Buttons */
percentBtn.addEventListener('click', () => togglePercentage(attributesChart));
logBtn.addEventListener('click', () => toggleLogScale(attributesChart));
donutBtn.addEventListener('click', () => toggleCutout(attributesChart));
sortBtn.addEventListener('click', () => toggleSort(attributesChart));
reverseBtn.addEventListener('click', () => toggleReverse(attributesChart));

/* Scrollbar - Attributes Buttons */
attributeBtns.forEach((btn, i) => handleAttributesBtns(btn, i));

/* Scrollbar - Scrolling */
rightArrowIcon.addEventListener('click', () => {
  chipsList.scrollLeft += 200;
  updateScrollbarIcons();
});

leftArrowIcon.addEventListener('click', () => {
  chipsList.scrollLeft -= 200;
  updateScrollbarIcons();
});

chipsList.addEventListener('scroll', updateScrollbarIcons);

chipsList.addEventListener('wheel', (e) => {
  e.preventDefault();
  chipsList.scrollLeft += e.deltaY * 2.5;
  updateScrollbarIcons();
});

chipsList.addEventListener('mousedown', () => {
  isDragging = true;
});

chipsList.addEventListener('mousemove', (e) => {
  if (!isDragging) return;
  chipsList.classList.add('scrollbar__chips--dragging');
  chipsList.scrollBy(-e.movementX, 0);
});

document.addEventListener('mouseup', () => {
  isDragging = false;
  chipsList.classList.remove('scrollbar__chips--dragging');
});

window.addEventListener('resize', updateScrollbarIcons);

/* Select first/second attribute of correlation matrix */
selectOne.addEventListener('change', () => handleSelectOne());
selectTwo.addEventListener('change', () => handleSelectTwo());

/* Modal window for correlations help */
helpBtn.addEventListener('click', openModal);
closeBtn.addEventListener('click', closeModal);
overlay.addEventListener('click', closeModal);

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape' && !helpModal.classList.contains('modal--hidden')) {
    closeModal();
  }
});

/* Darkmode Button */
darkmodeBtn.addEventListener('click', () => handleDarkmodeBtn());

/* Check if array contains only numbers */
function isArrayOfNumbers(array) {
  return array.every((item) => typeof item === 'number');
}

///////////////////////////////////////////////
// INITIALIZATION

updateChartJsConfig();
loadReport();
formatSummaryStats();
updateScrollbarIcons();
