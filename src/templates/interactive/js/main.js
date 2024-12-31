'use strict';

///////////////////////////////////////////////
// GLOBAL VARIABLES

const profiles = JSON.parse(`{{ attribute_profiles | tojson  }}`); // data from python
const correlations = JSON.parse(`{{ correlations_data | tojson }}`); // data from python
let isDragging = false; // attributes scrollbar mouse dragging indicator
let chartColors = null; // color scheme for Chart.js
let isPrintView = false; // all at once view indicator

///////////////////////////////////////////////
// ELEMENTS

/* Header */
const heading = document.querySelector('.heading-1');
const toggleViewBtn = document.querySelector('.btn--print');
const darkmodeBtn = document.querySelector('.btn--darkmode');
const navigations = document.querySelectorAll('.nav .btn');
const summaryNav = document.querySelector('.btn--summary');
const attributesNav = document.querySelector('.btn--attributes');
const correlationsNav = document.querySelector('.btn--correlations');

/* Pages */
const pages = document.querySelectorAll('.page');
const summaryPage = document.querySelector('.summary');
const attributesPage = document.querySelector('.attributes');
const correlationsPage = document.querySelector('.correlations');

/* Summary Page */
const totalAttributesStat = document.querySelector('.stats__value--attributes');
const totalRecordsStat = document.querySelector('.stats__value--records');
const totalMissStat = document.querySelector('.stats__value--miss');
const missingBtn = document.querySelector('.stats:has(.stats__value--miss)');

/* Modals */
const helpBtn = document.querySelector('.correlations .btn--help');
const excludedBtn = document.querySelector('.btn--excluded');
const modals = document.querySelectorAll('.modal');
const overlay = document.querySelector('.overlay');
const closeBtns = document.querySelectorAll('.modal__close');

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
  if (isPrintView) {
    document
      .querySelector(`.${page}`)
      .scrollIntoView({ behavior: 'smooth', block: 'start' });
    navigations.forEach((navEl) => navEl.classList.remove('btn--active'));
    document
      .querySelector(`.nav .btn[href="#${page}"]`)
      .classList.add('btn--active');
    return;
  }

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
        document.querySelector('.btn--attribute').classList.add('btn--active');
        updateStats(profiles[0]);
        const attributesCanvas = document.querySelector('.attributes .canvas');
        const box = attributesCanvas.closest('.box--chart');
        box
          .querySelector('.btn--bar')
          .addEventListener('click', () => handleBarBtn(0));
        box
          .querySelector('.btn--hbar')
          .addEventListener('click', () => handleHbarBtn(0));
        box
          .querySelector('.btn--pie')
          .addEventListener('click', () => handlePieBtn(0));
        box
          .querySelector('.btn--minitable')
          .addEventListener('click', () => handleMinitableBtn(0));
        box
          .querySelector('.btn--missings')
          .addEventListener('click', () => handleMissingsBtn(0));
        box
          .querySelector('.btn--percentage')
          .addEventListener('click', () => togglePercentage(0));
        box
          .querySelector('.btn--log')
          .addEventListener('click', () => toggleLogScale(0));
        box
          .querySelector('.btn--donut')
          .addEventListener('click', () => toggleCutout(0));
        box
          .querySelector('.btn--sort')
          .addEventListener('click', () => toggleSort(0));
        box
          .querySelector('.btn--reverse')
          .addEventListener('click', () => toggleReverse(0));
        renderGraph(attributesCanvas, 'bar');
      }
      break;

    case 'correlations':
      correlationsPage.classList.add('page--active');
      correlationsNav.classList.add('btn--active');
      renderMatrix(document.querySelector('.canvas--correlations'));
      break;
  }
}

// Update active state of navigation links based on scroll position
function updateActiveNav() {
  const sections = document.querySelectorAll('.page');
  const options = {
    root: null,
    rootMargin: '-52px 0px 0px 0px',
    threshold: 0.5,
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const sectionId = entry.target.id;
        navigations.forEach((navEl) => {
          const isActive = navEl.getAttribute('href') === `#${sectionId}`;
          navEl.classList.toggle('btn--active', isActive);
        });
      }
    });
  }, options);

  sections.forEach((section) => {
    observer.observe(section);
  });
}

// Display or hide scrollbar nav arrows at the attributes page
function updateScrollbarIcons() {
  const chipsList = document.querySelector('.scrollbar__chips');
  const scrollLeft = chipsList.scrollLeft;
  const max = chipsList.scrollWidth - chipsList.clientWidth - 10;
  document
    .querySelector('.scrollbar__arrow--left')
    .classList.toggle('scrollbar__arrow--active', scrollLeft >= 10);
  document
    .querySelector('.scrollbar__arrow--right')
    .classList.toggle('scrollbar__arrow--active', scrollLeft < max);
}

// Update stats boxes at the attributes pages
function updateStats(profile) {
  const attributeName = profile.attribute;
  const title = attributeName
    .replaceAll('_', ' ')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
  document.querySelector('.box--chart .heading-2').innerText = title;

  document.querySelector(
    '.stats__value--missing'
  ).innerHTML = `${(+profile.missing).toLocaleString()} <span>(${(
    (profile.missing /
      (profile.counts.reduce((a, c) => a + c, 0) + profile.missing)) *
    100
  ).toFixed(2)}%)</span>`;
  document.querySelector('.stats__value--categories').innerText =
    profile.categories.length.toLocaleString();

  const maxIndex = profile.counts.indexOf(Math.max(...profile.counts));
  const minIndex = profile.counts.indexOf(Math.min(...profile.counts));

  document.querySelector('.stats__value--most').innerHTML = `${
    profile.categories[maxIndex]
  } <span>(${profile.percentages[maxIndex].toFixed(2)}%)</span>`;
  document.querySelector('.stats__value--least').innerHTML = `${
    profile.categories[minIndex]
  } <span>(${profile.percentages[minIndex].toFixed(2)}%)</span>`;
}

// Render graph according to selected attribute
function renderGraph(canvas, type) {
  const chart = Chart.getChart(canvas);
  if (chart) chart.destroy();

  const data = profiles[canvas.dataset.attribute];

  const box = canvas.closest('.box');
  const missingsBtn = box.querySelector('.attributes .btn--missings');
  if (data.detected.length > 0) missingsBtn.classList.remove('btn--hidden');
  else missingsBtn.classList.add('btn--hidden');

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
function toggleCutout(index) {
  const canvas = document.querySelector(
    `.canvas--attributes[data-attribute="${index}"]`
  );
  const chart = Chart.getChart(canvas);
  if (chart.options.type !== 'pie') return;
  const box = canvas.closest('.box');
  box.querySelector('.btn--donut').classList.toggle('btn--active');
  chart.options.cutout = chart?.options?.cutout === 0 ? '50%' : 0;
  chart.update();
}

// Switch between percentage and nominal scale
function togglePercentage(index) {
  const canvas = document.querySelector(
    `.canvas--attributes[data-attribute="${index}"]`
  );
  const box = canvas.closest('.box');
  const chart = Chart.getChart(canvas);

  if (!['bar', 'pie'].includes(chart.options.type)) return;

  const percentBtn = box.querySelector('.btn--percentage');
  const isPercentage = percentBtn.classList.contains('btn--active');
  percentBtn.classList.toggle('btn--active');
  const valueAxis = chart.options.indexAxis === 'x' ? 'y' : 'x';

  if (isPercentage) {
    chart.data.datasets[0].data = [...chart.data.datasets[0].counts];
    delete chart.options.plugins.tooltip.callbacks.label;
    if (chart.options.type === 'bar') {
      delete chart.options.scales[valueAxis].ticks.callback;
    }
  }

  if (!isPercentage) {
    chart.data.datasets[0].data = [...chart.data.datasets[0].percentages];
    chart.options.plugins.tooltip.callbacks.label = (context) =>
      `${context.dataset.label}: ${context.raw} %`;
    if (chart.options.type === 'bar') {
      chart.options.scales[valueAxis].ticks.callback = (value) => `${value} %`;
    }
  }

  chart.update();
}

// Switch between logarithmic and normal scale
function toggleLogScale(index) {
  const canvas = document.querySelector(
    `.canvas--attributes[data-attribute="${index}"]`
  );
  const box = canvas.closest('.box');
  const chart = Chart.getChart(canvas);
  if (chart.options.type !== 'bar') return;
  box.querySelector('.btn--log').classList.toggle('btn--active');
  const valueAxis = chart.options.indexAxis === 'x' ? 'y' : 'x';
  chart.options.scales[valueAxis].type =
    chart.options.scales[valueAxis].type !== 'logarithmic'
      ? 'logarithmic'
      : 'linear';
  chart.update();
}

/* Check if array contains only numbers */
function isArrayOfNumbers(array) {
  return array.every((item) => typeof item === 'number');
}

// Sort chart alphabeticaly
function toggleSort(index) {
  const canvas = document.querySelector(
    `.canvas--attributes[data-attribute="${index}"]`
  );
  const box = canvas.closest('.box');
  const chart = Chart.getChart(canvas);
  const sortBtn = box.querySelector('.btn--sort');

  box.querySelector('.btn--reverse').classList.remove('btn--active');

  if (
    !box.querySelector('.minitable').classList.contains('minitable--hidden')
  ) {
    return sortMiniTable(index, box, chart);
  }

  if (sortBtn.classList.contains('btn--active')) {
    sortBtn.classList.remove('btn--active');
    const isPercentageScale = document
      .querySelector('.attributes .btn--percentage')
      .classList.contains('btn--active');
    const profile = profiles[chart.canvas.dataset.attribute];
    chart.config.data.labels = [...profile.categories];
    chart.config.data.datasets[0].data = isPercentageScale
      ? [...profile.percentages]
      : [...profile.counts];
    chart.config.data.datasets[0].counts = [...profile.counts];
    chart.config.data.datasets[0].percentages = [...profile.percentages];
    return chart.update();
  }

  sortBtn.classList.add('btn--active');

  const data = chart.config.data.datasets[0].data.map((data, i) => [
    chart.config.data.labels[i],
    data,
    chart.config.data.datasets[0].counts[i],
    chart.config.data.datasets[0].percentages[i],
  ]);

  const sorted = isArrayOfNumbers(data.map((v) => v[0]))
    ? data.slice().sort((a, b) => a[0] - b[0])
    : data.slice().sort((a, b) => String(a[0]).localeCompare(String(b[0])));

  chart.config.data.datasets[0].data = sorted.map((data) => data[1]);
  chart.config.data.labels = sorted.map((data) => data[0]);
  chart.config.data.datasets[0].counts = sorted.map((data) => data[2]);
  chart.config.data.datasets[0].percentages = sorted.map((data) => data[3]);

  chart.update();
}

// Sort minitable alphabeticaly
function sortMiniTable(index, box, chart) {
  const minitableEl = box.querySelector('.minitable');
  const header = minitableEl.querySelector('.minitable__header');
  if (header.innerText.includes('Missing')) return;
  const rows = Array.from(minitableEl.querySelectorAll('.minitable__row'));
  const sortBtn = box.querySelector('.btn--sort');

  if (sortBtn.classList.contains('btn--active')) {
    sortBtn.classList.remove('btn--active');
    const profile = profiles[index];
    const rows = [...profile.categories].map(
      (cat, i) =>
        `<li class='minitable__row'>
      <div class='minitable__field'>${cat}</div>
      <div class='minitable__field'>${profile.counts[i]}</div>
      <div class='minitable__field'>${profile.percentages[i]} %
        </div>
        </li>`
    );
    minitableEl.innerHTML = header.outerHTML + rows.join('\n');
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

  minitableEl.innerHTML = header.outerHTML + sortedHtml;
}

// Reverse chart columns (data) order
function toggleReverse(index) {
  const canvas = document.querySelector(
    `.canvas--attributes[data-attribute="${index}"]`
  );
  const box = canvas.closest('.box');
  const chart = Chart.getChart(canvas);
  box.querySelector('.btn--reverse').classList.toggle('btn--active');

  const minitableEl = box.querySelector('.minitable');
  if (!minitableEl.classList.contains('minitable--hidden')) {
    return reverseMinitable(minitableEl);
  }

  chart.config.data.datasets[0].data.reverse();
  chart.config.data.datasets[0].counts.reverse();
  chart.config.data.datasets[0].percentages.reverse();
  chart.config.data.labels.reverse();
  chart.update();
}

// Reverse rows in minitable
function reverseMinitable(minitableEl) {
  const header = minitableEl.querySelector('.minitable__header');
  const rows = minitableEl.querySelectorAll('.minitable__row');
  const reversedRows = Array.from(rows)
    .reverse()
    .map((row) => row.outerHTML)
    .join('');
  minitableEl.innerHTML = header.outerHTML + reversedRows;
}

// Copy chart to clipboard as PNG
async function copyChartToClipboard(button) {
  try {
    const box = button.closest('.box');
    const canvas = box.querySelector('canvas');
    const isDarkMode = document.documentElement.classList.contains('dark-mode');
    const originalBackgroundColor = canvas.style.backgroundColor;

    if (isDarkMode) {
      // For dark mode we need to add a dark background to the canvas
      const styles = getComputedStyle(document.documentElement);
      const darkBackgroundColor = styles.getPropertyValue('--color-grey-0');
      const tempCanvas = document.createElement('canvas');
      const tempContext = tempCanvas.getContext('2d');
      tempCanvas.width = canvas.width;
      tempCanvas.height = canvas.height;
      tempContext.fillStyle = darkBackgroundColor;
      tempContext.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
      tempContext.drawImage(canvas, 0, 0);
      const tempBlob = await new Promise((resolve) =>
        tempCanvas.toBlob(resolve)
      );
      const tempImage = new Image();
      tempImage.src = URL.createObjectURL(tempBlob);
      await new Promise((resolve) => {
        tempImage.onload = () => {
          const context = canvas.getContext('2d');
          context.drawImage(tempImage, 0, 0);
          resolve();
        };
      });
    }

    const blob = await new Promise((resolve) => canvas.toBlob(resolve));
    const item = new ClipboardItem({ 'image/png': blob });
    await navigator.clipboard.write([item]);
    canvas.style.backgroundColor = originalBackgroundColor;
    showToast('Chart copied to clipboard!');
  } catch (err) {
    console.error('Failed to copy chart: ', err);
    alert('Failed to copy chart!');
  }
}

// Show toast notification
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.innerText = message;
  toast.classList.add('toast--visible');
  setTimeout(() => {
    toast.classList.remove('toast--visible');
  }, 3000);
}

// Render correlations matrix
function renderMatrix(canvas) {
  const chart = Chart.getChart(canvas);
  if (chart) chart.destroy();

  const styles = getComputedStyle(document.documentElement);
  const chartColorPositive = styles.getPropertyValue('--color-two');
  const chartColorNegative = styles.getPropertyValue('--color-one');
  const data = correlations[canvas.dataset.correlations];
  const maxCorrelation = Math.max(...data.map((corr) => corr.v));
  const [attributeOne, attributeTwo] = canvas.dataset.correlations.split(' x ');

  const labelsX =
    attributeOne === 'Cramers V' ||
    attributeOne === 'Spearman Rank' ||
    attributeOne === 'Theils U'
      ? profiles.map((p) => p.attribute)
      : profiles.find((p) => p.attribute === attributeOne).categories;

  const labelsY =
    attributeOne === 'Cramers V' ||
    attributeOne === 'Spearman Rank' ||
    attributeOne === 'Theils U'
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
          const value = context.dataset.data[context.dataIndex].v;
          const transparency =
            Math.abs(value) /
            (attributeOne === 'Spearman Rank' ? 1 : maxCorrelation);
          return value < 0
            ? changeTransparency(chartColorNegative, transparency)
            : changeTransparency(chartColorPositive, transparency);
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
            title: () =>
              `${
                document.querySelector('.correlations .box .heading-2')
                  .innerText
              }`,
          },
        },
      },
    },
    plugins: [
      colorScaleLegend(
        attributeOne === 'Spearman Rank' ? -1 : 0,
        attributeOne === 'Spearman Rank' ? 1 : maxCorrelation,
        chartColorPositive,
        chartColorNegative,
        attributeOne
      ),
    ],
  };

  return new Chart(canvas, config);
}

// ColorScaleLegend plugin for correlation matrix
function colorScaleLegend(
  min,
  max,
  chartColorPositive,
  chartColorNegative,
  correlationType
) {
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
      if (correlationType === 'Spearman Rank') {
        gradient.addColorStop(0, changeTransparency(chartColorPositive, 1));
        gradient.addColorStop(0.5, changeTransparency(chartColorPositive, 0));
        gradient.addColorStop(0.5, changeTransparency(chartColorNegative, 0));
        gradient.addColorStop(1, changeTransparency(chartColorNegative, 1));
      } else {
        gradient.addColorStop(0, changeTransparency(chartColorPositive, 1));
        gradient.addColorStop(1, changeTransparency(chartColorPositive, 0));
      }

      ctx.fillStyle = gradient;
      ctx.fillRect(right + layout.padding.right - 30, top, 15, height);

      const styles = getComputedStyle(document.documentElement);

      ctx.font = '12px Poppins';
      ctx.textAlign = 'center';
      ctx.fillStyle = styles.getPropertyValue('--color-grey-700');

      ctx.fillText(
        max.toFixed(2),
        right + layout.padding.right - 22.5,
        top - 10
      );

      ctx.fillText(
        min.toFixed(2),
        right + layout.padding.right - 22.5,
        bottom + 12
      );
    },
  };
}

// Open modal window with help for correlations
function openModal(className) {
  const modal = document.querySelector(className);
  modal.classList.remove('modal--hidden');
  overlay.classList.remove('overlay--hidden');
}

// Close modal window with help for correlations
function closeModal() {
  modals.forEach((modal) => {
    modal.classList.add('modal--hidden');
  });
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

// Update chart colors for darkmode or lightmode
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

    const chartColorPositive = styles.getPropertyValue('--color-two');
    const chartColorNegative = styles.getPropertyValue('--color-one');

    chart.data.datasets[0].backgroundColor = (context) => {
      const value = context.dataset.data[context.dataIndex].v;
      const transparency =
        Math.abs(value) /
        (chart.options.plugins.tooltip.callbacks.label === 'Spearman Rank'
          ? 1
          : maxCorrelation);
      return value < 0
        ? changeTransparency(chartColorNegative, transparency)
        : changeTransparency(chartColorPositive, transparency);
    };

    chart.config.plugins[0] = colorScaleLegend(
      chart.options.plugins.tooltip.callbacks.label === 'Spearman Rank'
        ? -1
        : 0,
      chart.options.plugins.tooltip.callbacks.label === 'Spearman Rank'
        ? 1
        : maxCorrelation,
      chartColorPositive,
      chartColorNegative,
      chart.options.plugins.tooltip.callbacks.label
    );
  }

  if (chartType === 'pie') {
    chart.options.borderColor = styles.getPropertyValue('--color-grey-0');
  }

  chart.options.plugins.legend.labels.color =
    styles.getPropertyValue('--color-grey-700');

  if (chartType === 'bar') {
    chart.config.data.datasets[0].backgroundColor =
      chartColors[chart.canvas.dataset.attribute % chartColors.length];
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
    totalAttributesStat.innerText.toLocaleString();
  totalRecordsStat.innerText = (+totalRecordsStat.innerText).toLocaleString();
  totalMissStat.innerHTML = `${(+totalMissStat.innerText
    .split('(')[0]
    .trim()).toLocaleString()} <span>(${
    totalMissStat.innerText.split('(')[1]
  }</span>`;
}

// Render bar chart at attributes page
function handleBarBtn(index) {
  const canvas = document.querySelector(
    `.canvas--attributes[data-attribute="${index}"]`
  );
  const box = canvas.closest('.box');
  box.querySelector('.minitable').classList.add('minitable--hidden');
  canvas.classList.remove('canvas--hidden');
  renderGraph(canvas, 'bar');
  box
    .querySelectorAll('.btn')
    .forEach((btn) => btn.classList.remove('btn--active'));
  box.querySelector('.btn--bar').classList.add('btn--active');
  box.querySelector('.btn--percentage').classList.remove('btn--hidden');
  box.querySelector('.btn--log').classList.remove('btn--hidden');
  box.querySelector('.btn--donut').classList.add('btn--hidden');
  box.querySelector('.btn--copy').classList.remove('btn--hidden');
}

// Render horizontal bar chart
function handleHbarBtn(index) {
  const canvas = document.querySelector(
    `.canvas--attributes[data-attribute="${index}"]`
  );
  const box = canvas.closest('.box');
  box.querySelector('.minitable').classList.add('minitable--hidden');
  canvas.classList.remove('canvas--hidden');
  renderGraph(canvas, 'hbar');
  box
    .querySelectorAll('.btn')
    .forEach((btn) => btn.classList.remove('btn--active'));
  box.querySelector('.type .btn--hbar').classList.add('btn--active');
  box.querySelector('.btn--percentage').classList.remove('btn--hidden');
  box.querySelector('.btn--log').classList.remove('btn--hidden');
  box.querySelector('.btn--donut').classList.add('btn--hidden');
  box.querySelector('.btn--copy').classList.remove('btn--hidden');
}

// Render pie chart at attributes page
function handlePieBtn(index) {
  const canvas = document.querySelector(
    `.canvas--attributes[data-attribute="${index}"]`
  );
  const box = canvas.closest('.box');
  box.querySelector('.minitable').classList.add('minitable--hidden');
  canvas.classList.remove('canvas--hidden');
  renderGraph(canvas, 'pie');
  box
    .querySelectorAll('.btn')
    .forEach((btn) => btn.classList.remove('btn--active'));
  box.querySelector('.btn--pie').classList.add('btn--active');
  box.querySelector('.btn--donut').classList.remove('btn--hidden');
  box.querySelector('.btn--percentage').classList.remove('btn--hidden');
  box.querySelector('.btn--log').classList.add('btn--hidden');
  box.querySelector('.btn--copy').classList.remove('btn--hidden');
}

// Header for minitable of attributes
const minitableHeader = `<li class='minitable__header'>
<div class='minitable__field'>Categories</div>
<div class='minitable__field'>Counts</div>
<div class='minitable__field'>Percentage</div></li>`;

// Render minitable at attributes page
function handleMinitableBtn(index) {
  const canvas = document.querySelector(
    `.canvas--attributes[data-attribute="${index}"]`
  );
  const box = canvas.closest('.box');
  box
    .querySelectorAll('.btn')
    .forEach((btn) => btn.classList.remove('btn--active'));
  box.querySelector('.btn--minitable').classList.add('btn--active');
  box.querySelector('.btn--percentage').classList.add('btn--hidden');
  box.querySelector('.btn--log').classList.add('btn--hidden');
  box.querySelector('.btn--donut').classList.add('btn--hidden');
  box.querySelector('.btn--copy').classList.add('btn--hidden');
  const chart = Chart.getChart(canvas);
  if (chart) chart.destroy();
  canvas.classList.add('canvas--hidden');
  const profile = profiles[canvas.dataset.attribute];
  const rows = profile.categories.map(
    (cat, i) =>
      `<li class='minitable__row'>
    <div class='minitable__field'>${cat}</div>
    <div class='minitable__field'>${profile.counts[i]}</div>
    <div class='minitable__field'>${profile.percentages[i]} %
      </div>
      </li>`
  );
  const minitableEl = box.querySelector('.minitable');
  minitableEl.innerHTML = minitableHeader + rows.join('\n');
  minitableEl.classList.remove('minitable--hidden');
}

// Header for minitable of missings
const missingsHeader = `<li class='minitable__header'>
<div class='minitable__field'>Missing values</div>
<div class='minitable__field'>Counts</div>
<div class='minitable__field'>Percentage</div></li>`;

// Render missings table at attributes page
function handleMissingsBtn(index) {
  const canvas = document.querySelector(
    `.canvas--attributes[data-attribute="${index}"]`
  );
  const box = canvas.closest('.box');

  const profile = profiles[canvas.dataset.attribute];
  if (profile.detected.length === 0) return;

  box
    .querySelectorAll('.btn')
    .forEach((btn) => btn.classList.remove('btn--active'));
  box.querySelector('.btn--missings').classList.add('btn--active');
  box.querySelector('.btn--percentage').classList.add('btn--hidden');
  box.querySelector('.btn--log').classList.add('btn--hidden');
  box.querySelector('.btn--donut').classList.add('btn--hidden');
  box.querySelector('.btn--copy').classList.add('btn--hidden');

  canvas.classList.add('canvas--hidden');
  const rows = profile.detected.map(
    (det, i) =>
      `<li class='minitable__row'>
    <div class='minitable__field'>${det === '' ? 'Blank values' : det}</div>
    <div class='minitable__field'>${profile.replaced[i]}</div>
    <div class='minitable__field'>${(
      (profile.replaced[i] /
        (profile.counts.reduce((a, c) => a + c, 0) + profile.missing)) *
      100
    ).toFixed(2)} %
      </div>
      </li>`
  );
  const minitableEl = box.querySelector('.minitable');
  minitableEl.innerHTML = missingsHeader + rows.join('\n');
  minitableEl.classList.remove('minitable--hidden');
}

// Switch profiled attribute at attributes page
function handleAttributesBtns(btn, i) {
  btn.addEventListener('click', () => {
    document
      .querySelectorAll('.btn--attribute')
      .forEach((btn) => btn.classList.remove('btn--active'));
    btn.classList.add('btn--active');
    document
      .querySelectorAll('.attributes .type .btn')
      .forEach((btn) => btn.classList.remove('btn--active'));
    document
      .querySelector('.attributes .btn--bar')
      .classList.add('btn--active');
    document
      .querySelectorAll('.attributes .options .btn')
      .forEach((btn) => btn.classList.remove('btn--active'));
    document
      .querySelector('.attributes .btn--percentage')
      .classList.remove('btn--hidden');
    document
      .querySelector('.attributes .btn--log')
      .classList.remove('btn--hidden');
    document
      .querySelector('.attributes .btn--donut')
      .classList.add('btn--hidden');
    document
      .querySelector('.attributes .canvas')
      .classList.remove('canvas--hidden');
    updateStats(profiles[i]);
    document.querySelector('.minitable').classList.add('minitable--hidden');
    const attributesCanvas = document.querySelector('.attributes .canvas');
    const box = attributesCanvas.closest('.box--chart');
    box
      .querySelector('.btn--bar')
      .addEventListener('click', () => handleBarBtn(i));
    box
      .querySelector('.btn--hbar')
      .addEventListener('click', () => handleHbarBtn(i));
    box
      .querySelector('.btn--pie')
      .addEventListener('click', () => handlePieBtn(i));
    box
      .querySelector('.btn--minitable')
      .addEventListener('click', () => handleMinitableBtn(i));
    box
      .querySelector('.btn--missings')
      .addEventListener('click', () => handleMissingsBtn(i));
    box
      .querySelector('.btn--percentage')
      .addEventListener('click', () => togglePercentage(i));
    box
      .querySelector('.btn--log')
      .addEventListener('click', () => toggleLogScale(i));
    box
      .querySelector('.btn--donut')
      .addEventListener('click', () => toggleCutout(i));
    box
      .querySelector('.btn--sort')
      .addEventListener('click', () => toggleSort(i));
    box
      .querySelector('.btn--reverse')
      .addEventListener('click', () => toggleReverse(i));
    attributesCanvas.setAttribute('data-attribute', i);
    renderGraph(attributesCanvas, 'bar');
  });
}

// Handle first attribute select at correlation page
function handleSelectOne() {
  const selectOne = document.querySelector('.correlations .select--one');
  const individualCorrelations =
    selectOne.value !== 'Cramers V' &&
    selectOne.value !== 'Spearman Rank' &&
    selectOne.value !== 'Theils U';
  const selectTwo = document.querySelector('.correlations .select--two');
  selectTwo.classList.toggle('select--hidden', !individualCorrelations);
  document
    .querySelector('.correlations .divider')
    .classList.toggle('divider--hidden', !individualCorrelations);

  const newValue = individualCorrelations
    ? `${selectOne.value} x ${selectTwo.value}`
    : selectOne.value;

  document.querySelector('.correlations .box .heading-2').innerText = newValue;
  const correlationsCanvas = document.querySelector('.canvas--correlations');
  correlationsCanvas.setAttribute('data-correlations', newValue);
  renderMatrix(correlationsCanvas);
}

// Handle second attribute select at correlation page
function handleSelectTwo() {
  const selectOne = document.querySelector('.correlations .select--one');
  const selectTwo = document.querySelector('.correlations .select--two');
  const individualCorrelations =
    selectOne.value !== 'Cramers V' &&
    selectOne.value !== 'Spearman Rank' &&
    selectOne.value !== 'Theils U';

  const newValue = individualCorrelations
    ? `${selectOne.value} x ${selectTwo.value}`
    : selectOne.value;

  document.querySelector('.correlations .box .heading-2').innerText = newValue;
  const correlationsCanvas = document.querySelector('.canvas--correlations');
  correlationsCanvas.setAttribute('data-correlations', newValue);
  renderMatrix(correlationsCanvas);
}

// Handle darkmode toggle
function handleDarkmodeBtn() {
  const sunIcon = `{% include './img/sun.svg' %}`;
  const moonIcon = `{% include './img/moon.svg' %}`;

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

  document.querySelectorAll('canvas').forEach((canvas) => {
    const chart = Chart.getChart(canvas);
    if (chart) updateChartColors(chart);
  });
}

// Calculate stats for a given profile
function calculateStats(profile) {
  const attributeName = profile.attribute;
  const title = attributeName
    .replaceAll('_', ' ')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

  const missing = `${(+profile.missing).toLocaleString()} <span>(${(
    (profile.missing /
      (profile.counts.reduce((a, c) => a + c, 0) + profile.missing)) *
    100
  ).toFixed(2)}%)</span>`;
  const categoriesCount = profile.categories.length.toLocaleString();

  const maxIndex = profile.counts.indexOf(Math.max(...profile.counts));
  const minIndex = profile.counts.indexOf(Math.min(...profile.counts));

  const mostFrequent = `${
    profile.categories[maxIndex]
  } <span>(${profile.percentages[maxIndex].toFixed(2)}%)</span>`;
  const leastFrequent = `${
    profile.categories[minIndex]
  } <span>(${profile.percentages[minIndex].toFixed(2)}%)</span>`;

  return {
    title,
    missing,
    categoriesCount,
    mostFrequent,
    leastFrequent,
  };
}

// Handle print/interactive view toggle
function handleToggleView() {
  isPrintView = !isPrintView;

  if (isPrintView) {
    document.querySelector('.header').classList.add('header--sticky');
    pages.forEach((pageEl) => pageEl.classList.add('page--active'));
    toggleViewBtn.innerHTML = `{% include './img/interactive.svg' %}`;

    const attributesContainer = document.querySelector('.attributes .content');
    attributesContainer.innerHTML = '';

    // Render attributes boxes
    profiles.forEach((profile, index) => {
      const { title, categoriesCount, mostFrequent, leastFrequent, missing } =
        calculateStats(profile);
      const boxHtml = `
        <div class="box box--chart">
          <div class="settings">
            <h2 class="heading-2">${title}</h2>
            <div class="type">
              <button class="btn btn--icon btn--bar btn--active">{% include './img/bar.svg' %}</button>
              <button class="btn btn--icon btn--hbar">{% include './img/hbar.svg' %}</button>
              <button class="btn btn--icon btn--pie">{% include './img/pie.svg' %}</button>
              <button class="btn btn--icon btn--minitable">{% include './img/table.svg' %}</button>
              <button class="btn btn--icon btn--missings btn--hidden">{% include './img/error.svg' %}</button>
            </div>
            <div class="options">
              <button class="btn btn--icon btn--copy" title="copy">{% include './img/copy.svg' %}</button>
              <button class="btn btn--icon btn--percentage" title="percentage">{% include './img/percentage.svg' %}</button>
              <button class="btn btn--icon btn--log" title="logarithmic scale">{% include './img/log.svg' %}</button>
              <button class="btn btn--icon btn--donut btn--hidden" title="donut">{% include './img/donut.svg' %}</button>
              <button class="btn btn--icon btn--sort" title="sort">{% include './img/sort.svg' %}</button>
              <button class="btn btn--icon btn--reverse" title="reverse">{% include './img/reverse.svg' %}</button>
            </div>
          </div>
          <div class="print">
            <div class="stats--print">
              <div class="box stats">
                <div class="stats__icon stats__icon--categories">{% include './img/categories.svg' %}</div>
                <h5 class="stats__label">Categories</h5>
                <p class="stats__value stats__value--categories">
                  ${categoriesCount}
                </p>
              </div>
              <div class="box stats">
                <div class="stats__icon stats__icon--most">{% include './img/most.svg' %}</div>
                <h5 class="stats__label">Most Frequent</h5>
                <p class="stats__value stats__value--most">
                  ${mostFrequent}
                </p>
              </div>
              <div class="box stats">
                <div class="stats__icon stats__icon--least">{% include './img/least.svg' %}</div>
                <h5 class="stats__label">Least Frequent</h5>
                <p class="stats__value stats__value--least">
                  ${leastFrequent}
                </p>
              </div>
              <div class="box stats">
                <div class="stats__icon stats__icon--missing">{% include './img/missing.svg' %}</div>
                <h5 class="stats__label">Missing values</h5>
                <p class="stats__value stats__value--missing">
                  ${missing}
                </p>
              </div>
            </div>
            <div class="graph">
              <div style="max-width: 900px; max-height: 500px;">
                <canvas class="canvas canvas--attributes" data-attribute="${index}"></canvas>
              </div>
              <ul class="minitable minitable--hidden"></ul>
            </div>
          </div>
        </div>
      `;
      attributesContainer.insertAdjacentHTML('beforeend', boxHtml);

      // Render chart
      const canvas = document.querySelector(
        `.canvas--attributes[data-attribute="${index}"]`
      );
      renderGraph(canvas, 'bar');

      // Add event listeners to buttons
      const box = canvas.closest('.box--chart');
      box
        .querySelector('.btn--bar')
        .addEventListener('click', () => handleBarBtn(index));
      box
        .querySelector('.btn--hbar')
        .addEventListener('click', () => handleHbarBtn(index));
      box
        .querySelector('.btn--pie')
        .addEventListener('click', () => handlePieBtn(index));
      box
        .querySelector('.btn--minitable')
        .addEventListener('click', () => handleMinitableBtn(index));
      box
        .querySelector('.btn--missings')
        .addEventListener('click', () => handleMissingsBtn(index));
      box
        .querySelector('.stats:has(.stats__icon--missing)')
        .addEventListener('click', () => handleMissingsBtn(index));
      box
        .querySelector('.btn--copy')
        .addEventListener('click', () =>
          copyChartToClipboard(box.querySelector('.btn--copy'))
        );
      box
        .querySelector('.btn--percentage')
        .addEventListener('click', () => togglePercentage(index));
      box
        .querySelector('.btn--log')
        .addEventListener('click', () => toggleLogScale(index));
      box
        .querySelector('.btn--donut')
        .addEventListener('click', () => toggleCutout(index));
      box
        .querySelector('.btn--sort')
        .addEventListener('click', () => toggleSort(index));
      box
        .querySelector('.btn--reverse')
        .addEventListener('click', () => toggleReverse(index));
    });

    // Render overall correlations charts
    const renderOverallCorrelationChart = (correlationType) => {
      const overallHtml = `
        <div class="box box--chart">
          <div class="settings">
            <h2 class="heading-2">${correlationType}</h2>
          </div>
          <div class="graph">
            <div style="max-width: 900px; max-height: 500px;">
              <canvas class="canvas canvas--correlations" data-correlations="${correlationType}"></canvas>
            </div>
          </div>
        </div>
      `;
      correlationsPrintContainer.insertAdjacentHTML('beforeend', overallHtml);
      const overallCanvas = document.querySelector(
        `.correlations--print .canvas--correlations[data-correlations="${correlationType}"]`
      );
      renderMatrix(overallCanvas);
    };

    // Render correlations charts
    const correlationsContent = document.querySelector(
      '.correlations .content'
    );
    correlationsContent.classList.add('content--hidden');

    const correlationsPrintContainer = document.createElement('div');
    correlationsPrintContainer.classList.add('correlations--print');
    document
      .querySelector('.correlations')
      .appendChild(correlationsPrintContainer);

    // Render Cramers V, Spearman Rank, and Theil's U correlations charts
    ['Cramers V', 'Spearman Rank', 'Theils U'].forEach(
      renderOverallCorrelationChart
    );

    // Render individual correlations charts
    profiles.forEach((profile1) => {
      profiles.forEach((profile2) => {
        if (profile1.attribute !== profile2.attribute) {
          const correlationHtml = `
            <div class="box box--chart">
              <div class="settings">
                <h2 class="heading-2">${profile1.attribute} x ${profile2.attribute}</h2>
              </div>
              <div class="graph">
                <div style="max-width: 900px; max-height: 500px;">
                  <canvas class="canvas canvas--correlations" data-correlations="${profile1.attribute} x ${profile2.attribute}"></canvas>
                </div>
              </div>
            </div>
          `;
          correlationsPrintContainer.insertAdjacentHTML(
            'beforeend',
            correlationHtml
          );
          const correlationCanvas = document.querySelector(
            `.canvas--correlations[data-correlations="${profile1.attribute} x ${profile2.attribute}"]`
          );
          renderMatrix(correlationCanvas);
        }
      });
    });

    updateActiveNav();
  } else {
    pages.forEach((pageEl) => pageEl.classList.remove('page--active'));
    toggleViewBtn.innerHTML = `{% include './img/print.svg' %}`;

    const { title, categoriesCount, mostFrequent, leastFrequent, missing } =
      calculateStats(profiles[0]);

    document.querySelector('.attributes .content').innerHTML = `
          <div class="scrollbar scrollable-tabs-container">
            <div class="scrollbar__arrow scrollbar__arrow--left">
              {% include './img/left.svg' %}
            </div>
            <ul class="scrollbar__chips">
              {% for profile in attribute_profiles %}
              <li class="scrollbar__chip">
                <button class="btn btn--chip btn--attribute">
                  {{profile['attribute']}}
                </button>
              </li>
              {% endfor %}
            </ul>
            <div class="scrollbar__arrow scrollbar__arrow--right">
              {% include './img/right.svg' %}
            </div>
          </div>
          <div class="box stats">
            <div class="stats__icon stats__icon--categories">
              {% include './img/categories.svg' %}
            </div>
            <h5 class="stats__label">Categories</h5>
            <p class="stats__value stats__value--categories">${categoriesCount}</p>
          </div>
          <div class="box stats">
            <div class="stats__icon stats__icon--most">
              {% include './img/most.svg' %}
            </div>
            <h5 class="stats__label">Most Frequent</h5>
            <p class="stats__value stats__value--most">${mostFrequent}</p>
          </div>
          <div class="box stats">
            <div class="stats__icon stats__icon--least">
              {% include './img/least.svg' %}
            </div>
            <h5 class="stats__label">Least Frequent</h5>
            <p class="stats__value stats__value--least">${leastFrequent}</p>
          </div>
          <div class="box stats">
            <div class="stats__icon stats__icon--missing">
              {% include './img/missing.svg' %}
            </div>
            <h5 class="stats__label">Missing values</h5>
            <p class="stats__value stats__value--missing">${missing}</p>
          </div>
          <div class="box box--chart">
            <div class="settings">
              <h2 class="heading-2">${title}</h2>
              <div class="type">
                <button class="btn btn--icon btn--bar btn--active">
                  {% include './img/bar.svg' %}
                </button>
                <button class="btn btn--icon btn--hbar">
                  {% include './img/hbar.svg' %}
                </button>
                <button class="btn btn--icon btn--pie">
                  {% include './img/pie.svg' %}
                </button>
                <button class="btn btn--icon btn--minitable">
                  {% include './img/table.svg' %}
                </button>
                <button class="btn btn--icon btn--missings btn--hidden">
                  {% include './img/error.svg' %}
                </button>
              </div>
              <div class="options">
                <button
                  class="btn btn--icon btn--copy"
                  title="copy"
                >
                  {% include './img/copy.svg' %}
                </button>
                <button
                  class="btn btn--icon btn--percentage"
                  title="percentage"
                >
                  {% include './img/percentage.svg' %}
                </button>
                <button
                  class="btn btn--icon btn--log"
                  title="logarithmic scale"
                >
                  {% include './img/log.svg' %}
                </button>
                <button
                  class="btn btn--icon btn--donut btn--hidden"
                  title="donut"
                >
                  {% include './img/donut.svg' %}
                </button>
                <button class="btn btn--icon btn--sort" title="sort">
                  {% include './img/sort.svg' %}
                </button>
                <button class="btn btn--icon btn--reverse" title="reverse">
                  {% include './img/reverse.svg' %}
                </button>
              </div>
            </div>
            <div class="graph">
              <div style="max-width: 900px; max-height: 500px">
                <canvas
                  class="canvas canvas--attributes"
                  data-attribute="0"
                ></canvas>
              </div>
              <ul class="minitable minitable--hidden"></ul>
            </div>
          </div>`;

    document
      .querySelectorAll('.btn--attribute')
      .forEach((btn, i) => handleAttributesBtns(btn, i));

    const copyBtn = document.querySelector('.btn--copy');
    copyBtn.addEventListener('click', () => copyChartToClipboard(copyBtn));

    const correlationsPrintContainer = document.querySelector(
      '.correlations--print'
    );
    if (correlationsPrintContainer) {
      correlationsPrintContainer.remove();
    }
    const correlationsContent = document.querySelector(
      '.correlations .content'
    );
    correlationsContent.classList.remove('content--hidden');

    loadReport();
  }
}

///////////////////////////////////////////////
// EVENT HANDLERS

/* Page Navigation */
summaryNav.addEventListener('click', () => displayPage('summary'));
attributesNav.addEventListener('click', () => displayPage('attributes'));
correlationsNav.addEventListener('click', () => displayPage('correlations'));

function initEventHandlers() {
  /* Scrollbar - Attributes Buttons */
  document
    .querySelectorAll('.btn--attribute')
    .forEach((btn, i) => handleAttributesBtns(btn, i));

  /* Scrollbar - Scrolling */
  document
    .querySelector('.scrollbar__arrow--right svg')
    .addEventListener('click', () => {
      document.querySelector('.scrollbar__chips').scrollLeft += 200;
      updateScrollbarIcons();
    });

  document
    .querySelector('.scrollbar__arrow--left svg')
    .addEventListener('click', () => {
      document.querySelector('.scrollbar__chips').scrollLeft -= 200;
      updateScrollbarIcons();
    });

  const chipsList = document.querySelector('.scrollbar__chips');

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
  document
    .querySelector('.correlations .select--one')
    .addEventListener('change', handleSelectOne);
  document
    .querySelector('.correlations .select--two')
    .addEventListener('change', handleSelectTwo);

  /* Copy chart to clipboard */
  document.querySelectorAll('.btn--copy').forEach((btn) => {
    btn.addEventListener('click', () => {
      copyChartToClipboard(btn);
    });
  });
}

/* Opening modals */
if (excludedBtn) {
  excludedBtn.addEventListener('click', () => openModal('.modal--excluded'));
}
helpBtn.addEventListener('click', () => openModal('.modal--correlations'));
missingBtn.addEventListener('click', () => openModal('.modal--missings'));

/* Closing modals */
closeBtns.forEach((closeBtn) => {
  closeBtn.addEventListener('click', closeModal);
});
overlay.addEventListener('click', closeModal);

document.addEventListener('keydown', function (e) {
  if (
    e.key === 'Escape' &&
    !correlationsModal.classList.contains('modal--hidden')
  ) {
    closeModal();
  }
});

/* Darkmode Button */
darkmodeBtn.addEventListener('click', handleDarkmodeBtn);

/* Print or interactive view button */
toggleViewBtn.addEventListener('click', handleToggleView);

///////////////////////////////////////////////
// INITIALIZATION

initEventHandlers();
updateChartJsConfig();
loadReport();
formatSummaryStats();
updateScrollbarIcons();
updateActiveNav();
