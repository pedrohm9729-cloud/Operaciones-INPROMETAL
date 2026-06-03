// ==========================================================================
//  CONFIGURACIÓN DE RED Y ESTADO GLOBAL
// ==========================================================================
const API_BASE_URL = ''; // Rutas relativas locales para Hostinger.

// Trigger deploy: SSH enabled and password updated in Hostinger.
let allData = null;
let activeTab = 'dashboard';

// Columnas abstractas que usa el frontend (sin IDs reales de Coda)
// El backend resuelve estas claves a los column IDs internos.
const CODA_ABSTRACT_COLS = {
    'OT': {
        'codigo':       'codigo',
        'cliente':      'cliente',
        'estado':       'estado',
        'descripcion':  'descripcion',
        'precio_venta': 'precio_venta',
        'gastos':       'gastos',
        'utilidad':     'utilidad',
        'fecha_inicio': 'fecha_inicio',
        'fecha_entrega':'fecha_entrega'
    },
    'Facturas': {
        'factura':       'factura',
        'cliente':       'cliente',
        'monto':         'monto',
        'moneda':        'moneda',
        'estado':        'estado',
        'atraso':        'atraso',
        'fecha_pago':    'fecha_pago',
        'fecha_emision': 'fecha_emision',
        'ot':            'ot'
    },
    'GasCom': {
        'fecha':        'fecha',
        'proveedor':    'proveedor',
        'monto':        'monto',
        'moneda':       'moneda',
        'concepto':     'concepto',
        'categoria':    'categoria',
        'subcategoria': 'subcategoria',
        'ot':           'ot',
        'cantidad':     'cantidad'
    },
    'Personal': {
        'nombre':    'nombre',
        'dni':       'dni',
        'direccion': 'direccion',
        'celular':   'celular',
        'edad':      'edad',
        'bcp':       'bcp',
        'bbva':      'bbva'
    }
};

// IDs reales de columnas de Coda — usados SOLO para leer los datos devueltos por /api/data
// (el servidor nos los devuelve con sus IDs reales ya que leemos directo de Coda API)
const CODA_COLS = {
    'OT': {
        'codigo':       'c-pc5YuBXn96',
        'cliente':      'c-NKAKLScE0S',
        'estado':       'c-REo1Oizg0Y',
        'descripcion':  'c-hzJTUN6TGN',
        'precio_venta': 'c-r8UDJ5yyO2',
        'gastos':       'c-_XJ4HM6uby',
        'utilidad':     'c-6ywH8DA-ch',
        'fecha_inicio': 'c-3M9ac5NCTz',
        'fecha_entrega':'c-jWLKhW3vP9'
    },
    'Facturas': {
        'factura':       'c-JIV9w_1NWC',
        'cliente':       'c-q-6MtqAzZF',
        'monto':         'c-yFLHJCQPjq',
        'moneda':        'c-NHbA6tg43O',
        'estado':        'c-DzL5A7cfoh',
        'atraso':        'c-nCJ_HemjMC',
        'fecha_pago':    'c-w_xJeGpdz5',
        'fecha_emision': 'c-40nbQz-lkR',
        'ot':            'c-66AcWwCRS9'
    },
    'GasCom': {
        'fecha':        'c-61ofsG_OBR',
        'proveedor':    'c-NWRsEkGrw0',
        'monto':        'c-cYVuEll05n',
        'moneda':       'c-vXwEqLyp9Z',
        'concepto':     'c-481d5xGLOy',
        'categoria':    'c-wYCNse9QsV',
        'subcategoria': 'c-cJFDputTU7',
        'ot':           'c-VQAnY2FKEn',
        'cantidad':     'c-EeFbBKh7Ln'
    },
    'Personal': {
        'nombre':    'c-oZyrOfYoCD',
        'dni':       'c-L-ty03t3qT',
        'direccion': 'c-KbIEZZ_hS8',
        'celular':   'c-uoRQV9tLRA',
        'edad':      'c-pDPpvo92jx',
        'bcp':       'c-bYKecv_8AY',
        'bbva':      'c-rgm_mztIeA'
    }
};

// Instancias de Gráficos
let chartCategoriesInstance = null;
let chartMonthlyInstance = null;
const TC_USD_PEN = 3.75;

// Colores de las categorías de gastos
const CATEGORY_COLORS = {
    'Materiales e Insumos': '#3b82f6',
    'Equipos y Herramientas': '#06b6d4',
    'Seguridad': '#f43f5e',
    'Personal': '#10b981',
    'Operaciones': '#f59e0b',
    'Administracion': '#8b5cf6',
    'Financiero': '#ec4899',
    'Otro': '#64748b'
};

// ==========================================================================
//  INICIALIZACIÓN AL CARGAR LA PÁGINA
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    setupNavigation();
    setupFormsToggles();
    setupFormSubmissions();
    setupSync();
    fetchData();
    setupAIChat();

    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
        btnLogout.addEventListener('click', handleLogout);
    }
});

// ==========================================================================
//  HELPER: Redirección 401 centralizada
// ==========================================================================
async function fetchProtected(url, options = {}) {
    const fullUrl = url.startsWith('/api/') ? API_BASE_URL + url : url;
    
    // Si estamos en un dominio cruzado (CORS), requerimos enviar cookies de sesión
    if (API_BASE_URL) {
        options.credentials = 'include';
    }

    const res = await fetch(fullUrl, options);
    if (res && res.status === 401) {
        window.location.href = '/login.html';
        return null;
    }
    return res;
}

// ==========================================================================
//  NAVEGACIÓN (TABS CONTROLLER)
// ==========================================================================
function setupNavigation() {
    const tabs = {
        'btn-tab-dashboard': 'dashboard',
        'btn-tab-ots':       'ots',
        'btn-tab-invoices':  'invoices',
        'btn-tab-expenses':  'expenses',
        'btn-tab-personal':  'personal'
    };

    Object.entries(tabs).forEach(([btnId, tabName]) => {
        const element = document.getElementById(btnId);
        if (element) {
            element.addEventListener('click', () => switchTab(tabName));
        }
    });
}

function switchTab(tabName) {
    activeTab = tabName;

    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    const activeBtn = document.getElementById(`btn-tab-${tabName}`);
    if (activeBtn) activeBtn.classList.add('active');

    document.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));
    document.getElementById(`tab-${tabName}`).classList.remove('hidden');

    const syncArea = document.getElementById('header-sync-area');
    if (tabName === 'dashboard' || tabName === 'expenses') {
        syncArea.style.display = 'block';
    } else {
        syncArea.style.display = 'none';
    }

    const titles = {
        'dashboard': { title: 'Resumen Operativo',              subtitle: 'Consola de operaciones integrada con la base de datos Coda.' },
        'ots':       { title: 'Órdenes de Trabajo (OT)',        subtitle: 'Planificación de proyectos y control de presupuesto.' },
        'invoices':  { title: 'Cobranza y Facturación',         subtitle: 'Facturas pendientes, por cobrar y cuentas al día.' },
        'expenses':  { title: 'Gastos y Compras (GasCom)',       subtitle: 'Egresos vinculados al taller de metalmecánica.' },
        'personal':  { title: 'Personal de Taller',             subtitle: 'Fichas de trabajadores y cuentas bancarias.' }
    };

    document.getElementById('page-title').innerText = titles[tabName].title;
    document.querySelector('.header-subtitle').innerText = titles[tabName].subtitle;

    if (allData) renderActiveTab();
}

function renderActiveTab() {
    if (!allData) return;
    if (activeTab === 'dashboard') {
        calculateKPIs();
        renderCharts();
    } else if (activeTab === 'ots') {
        renderOTsTable();
    } else if (activeTab === 'invoices') {
        renderInvoicesTable();
        populateOTDropdown('inv-ot');
    } else if (activeTab === 'expenses') {
        renderExpensesTable();
        populateOTDropdown('exp-ot');
    } else if (activeTab === 'personal') {
        renderPersonalTable();
    }
}

// ==========================================================================
//  VISIBILIDAD DE FORMULARIOS (CREACIÓN)
// ==========================================================================
function setupFormsToggles() {
    const toggles = [
        { btnShow: 'btn-show-ot-form',       btnClose: 'btn-close-ot-form',       cardId: 'form-ot-card' },
        { btnShow: 'btn-show-invoice-form',   btnClose: 'btn-close-invoice-form',  cardId: 'form-invoice-card' },
        { btnShow: 'btn-show-expense-form',   btnClose: 'btn-close-expense-form',  cardId: 'form-expense-card' },
        { btnShow: 'btn-show-personal-form',  btnClose: 'btn-close-personal-form', cardId: 'form-personal-card' }
    ];

    toggles.forEach(t => {
        const btnShowEl  = document.getElementById(t.btnShow);
        const btnCloseEl = document.getElementById(t.btnClose);
        const cardEl     = document.getElementById(t.cardId);

        if (btnShowEl && cardEl) {
            btnShowEl.addEventListener('click', () => {
                cardEl.classList.remove('hidden');
                cardEl.scrollIntoView({ behavior: 'smooth' });
            });
        }
        if (btnCloseEl && cardEl) {
            btnCloseEl.addEventListener('click', () => cardEl.classList.add('hidden'));
        }
    });
}

// ==========================================================================
//  CARGA DE DATOS DESDE EL BACKEND
// ==========================================================================
async function fetchData() {
    document.getElementById('lbl-last-sync').innerText = 'Cargando...';
    try {
        const response = await fetchProtected('/api/data.php');
        if (!response) return; // Redirigido a login

        if (!response.ok) throw new Error('Error al conectar con la API');

        const resJson = await response.json();
        if (resJson.success) {
            allData = resJson;
            document.getElementById('lbl-last-sync').innerText = allData.last_sync || 'No registrado';
            renderActiveTab();
        } else {
            console.error('API Error:', resJson.error);
            document.getElementById('lbl-last-sync').innerText = 'Error de carga';
        }
    } catch (error) {
        console.error('Fetch Error:', error);
        document.getElementById('lbl-last-sync').innerText = 'Error de conexión';
    }
}

// Llenar listas desplegables de OTs en los formularios
function populateOTDropdown(dropdownId) {
    const select = document.getElementById(dropdownId);
    if (!select || !allData) return;

    const currentVal = select.value;
    select.innerHTML = select.id === 'inv-ot'
        ? '<option value="">Asocia una OT si corresponde</option>'
        : '<option value="">Ninguna (Gasto Administrativo / General)</option>';

    const ots = allData?.data?.OT || [];
    const colOT = CODA_COLS.OT.codigo;
    const sortedOts = [...ots].sort((a, b) => {
        return String(a.values[colOT] || '').localeCompare(String(b.values[colOT] || ''));
    });

    sortedOts.forEach(otRow => {
        const code = otRow.values[colOT];
        if (code) {
            const opt = document.createElement('option');
            opt.value = code;
            opt.innerText = code;
            select.appendChild(opt);
        }
    });

    select.value = currentVal;
}

// ==========================================================================
//  TAB 1: CÁLCULOS KPI & GRÁFICOS
// ==========================================================================
function calculateKPIs() {
    if (!allData) return;

    const ots      = allData?.data?.OT       || [];
    const facturas = allData?.data?.Facturas  || [];
    const gascom   = allData?.data?.GasCom    || [];
    const personal = allData?.data?.Personal  || [];

    // 1. OTs Activas
    const activeOtsCount = ots.filter(row => {
        const est = row.values[CODA_COLS.OT.estado];
        return est === 'ACTIVO' || est === 'PLANIFICADO';
    }).length;
    document.getElementById('kpi-active-ots').innerText = activeOtsCount;

    // 2. Facturas por Cobrar + 3. Egresos — iteración única sobre gascom
    let totalPendingSoles = 0;
    facturas.forEach(row => {
        const est = row.values[CODA_COLS.Facturas.estado];
        if (est === 'PENDIENTE' || est === 'DETRACCION PENDIENTE') {
            const monto  = parseFloat(row.values[CODA_COLS.Facturas.monto]) || 0;
            const moneda = row.values[CODA_COLS.Facturas.moneda] || 'Soles';
            totalPendingSoles += (moneda === 'Dolares' || moneda === 'Dólares') ? monto * TC_USD_PEN : monto;
        }
    });
    document.getElementById('kpi-pending-invoices').innerText = formatCurrency(totalPendingSoles, 'Soles');

    let totalExpensesSoles = 0;
    gascom.forEach(row => {
        const monto  = parseFloat(row.values[CODA_COLS.GasCom.monto]) || 0;
        const moneda = row.values[CODA_COLS.GasCom.moneda] || 'Soles';
        totalExpensesSoles += (moneda === 'Dolares' || moneda === 'Dólares') ? monto * TC_USD_PEN : monto;
    });
    document.getElementById('kpi-expenses-total').innerText = formatCurrency(totalExpensesSoles, 'Soles');

    // 4. Trabajadores
    document.getElementById('kpi-workers-count').innerText = personal.length;
}

// ==========================================================================
//  PARSEO ROBUSTO DE FECHAS DE CODA
// ==========================================================================
function parseFechaYearMonth(fechaStr) {
    if (!fechaStr) return null;
    const d = new Date(fechaStr);
    if (isNaN(d.getTime())) return null;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    return `${y}-${m}`;
}

function renderCharts() {
    if (!allData || activeTab !== 'dashboard') return;

    const gascom = allData?.data?.GasCom || [];

    // Iteración única sobre gascom para gráfico donut + gráfico mensual
    const catTotals     = {};
    const monthlyTotals = {};

    gascom.forEach(row => {
        const monto  = parseFloat(row.values[CODA_COLS.GasCom.monto]) || 0;
        const moneda = row.values[CODA_COLS.GasCom.moneda] || 'Soles';
        const montoEquiv = (moneda === 'Dolares' || moneda === 'Dólares') ? monto * TC_USD_PEN : monto;

        // Categorías
        const cat = row.values[CODA_COLS.GasCom.categoria] || 'Otro';
        catTotals[cat] = (catTotals[cat] || 0) + montoEquiv;

        // Mensual (parser robusto)
        const yearMonth = parseFechaYearMonth(row.values[CODA_COLS.GasCom.fecha]);
        if (yearMonth) {
            monthlyTotals[yearMonth] = (monthlyTotals[yearMonth] || 0) + montoEquiv;
        }
    });

    // --- Gráfico de Categorías (Donut) ---
    const catSorted   = Object.entries(catTotals).sort((a, b) => b[1] - a[1]);
    const catLabels   = catSorted.map(x => x[0]);
    const catData     = catSorted.map(x => Math.round(x[1] * 100) / 100);
    const catColorsArr = catLabels.map(cat => CATEGORY_COLORS[cat] || '#64748b');

    if (chartCategoriesInstance) chartCategoriesInstance.destroy();
    const ctxCat = document.getElementById('chart-categories').getContext('2d');
    chartCategoriesInstance = new Chart(ctxCat, {
        type: 'doughnut',
        data: {
            labels: catLabels,
            datasets: [{
                data: catData,
                backgroundColor: catColorsArr,
                borderWidth: 1,
                borderColor: '#0f172a'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#f8fafc', font: { family: 'Plus Jakarta Sans', size: 11 } }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` S/ ${ctx.raw.toLocaleString('es-PE', { minimumFractionDigits: 2 })}`
                    }
                }
            },
            cutout: '65%'
        }
    });

    // --- Gráfico de Tendencia Mensual (Línea) ---
    const monthsSorted  = Object.entries(monthlyTotals).sort((a, b) => a[0].localeCompare(b[0]));
    const displayMonths = monthsSorted.slice(-12);

    const nombresMeses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    const monthLabels  = displayMonths.map(x => {
        const [y, m] = x[0].split('-');
        return `${nombresMeses[parseInt(m) - 1]} ${y.substring(2)}`;
    });
    const monthData = displayMonths.map(x => Math.round(x[1] * 100) / 100);

    if (chartMonthlyInstance) chartMonthlyInstance.destroy();
    const ctxMonth = document.getElementById('chart-monthly').getContext('2d');
    chartMonthlyInstance = new Chart(ctxMonth, {
        type: 'line',
        data: {
            labels: monthLabels,
            datasets: [{
                data: monthData,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.08)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: '#3b82f6'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => ` S/ ${ctx.raw.toLocaleString('es-PE', { minimumFractionDigits: 2 })}`
                    }
                }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#94a3b8' } },
                y: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}

// ==========================================================================
//  TAB 2: ÓRDENES DE TRABAJO (RENDER & UPDATE)
// ==========================================================================
function renderOTsTable() {
    const tbody = document.getElementById('ots-table-body');
    tbody.innerHTML = '';

    const ots = allData?.data?.OT || [];

    if (ots.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center py-4 text-secondary">No hay órdenes de trabajo registradas en Coda.</td></tr>';
        return;
    }

    const colOT = CODA_COLS.OT.codigo;
    const sortedOts = [...ots].sort((a, b) => String(b.values[colOT] || '').localeCompare(String(a.values[colOT] || '')));

    sortedOts.forEach(row => {
        const val   = row.values;
        const rowId = row.id;
        const currentEstado = val[CODA_COLS.OT.estado] || 'ACTIVO';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${val[CODA_COLS.OT.fecha_inicio] || '-'}</td>
            <td><strong>${val[colOT] || '-'}</strong></td>
            <td>${val[CODA_COLS.OT.cliente] || '-'}</td>
            <td><small>${val[CODA_COLS.OT.descripcion] || '-'}</small></td>
            <td class="text-right">S/ ${(parseFloat(val[CODA_COLS.OT.precio_venta]) || 0).toFixed(2)}</td>
            <td class="text-right text-secondary">S/ ${(parseFloat(val[CODA_COLS.OT.gastos]) || 0).toFixed(2)}</td>
            <td class="text-right font-bold">S/ ${(parseFloat(val[CODA_COLS.OT.utilidad]) || 0).toFixed(2)}</td>
            <td>${val[CODA_COLS.OT.fecha_entrega] || '-'}</td>
            <td><span class="state-badge ot-${String(currentEstado).toLowerCase()}">${currentEstado}</span></td>
            <td>
                <div class="table-actions-cell">
                    <select class="select-table-status" data-rowid="${rowId}" data-prev-estado="${currentEstado}">
                        <option value="ACTIVO"      ${currentEstado === 'ACTIVO'      ? 'selected' : ''}>ACTIVO</option>
                        <option value="PLANIFICADO" ${currentEstado === 'PLANIFICADO' ? 'selected' : ''}>PLANIF.</option>
                        <option value="COMPLETADO"  ${currentEstado === 'COMPLETADO'  ? 'selected' : ''}>COMPLE.</option>
                        <option value="ENTREGADO"   ${currentEstado === 'ENTREGADO'   ? 'selected' : ''}>ENTREG.</option>
                        <option value="CANCELADO"   ${currentEstado === 'CANCELADO'   ? 'selected' : ''}>CANCEL.</option>
                    </select>
                    <button class="btn btn-danger btn-icon-only btn-delete-ot" data-rowid="${rowId}" title="Eliminar OT">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // Bind eventos select estado (con reverso en caso de fallo)
    tbody.querySelectorAll('.select-table-status').forEach(select => {
        select.addEventListener('change', async () => {
            const rowId     = select.getAttribute('data-rowid');
            const prevEstado = select.getAttribute('data-prev-estado');
            const nuevoEstado = select.value;
            const ok = await handleUpdateRow('OT', rowId, [{ key: 'estado', value: nuevoEstado }]);
            if (!ok) {
                select.value = prevEstado; // Revertir si falla
            } else {
                select.setAttribute('data-prev-estado', nuevoEstado);
            }
        });
    });

    tbody.querySelectorAll('.btn-delete-ot').forEach(btn => {
        btn.addEventListener('click', async () => {
            const rowId = btn.getAttribute('data-rowid');
            if (confirm('¿Estás seguro de que deseas eliminar esta Orden de Trabajo de Coda?')) {
                await handleDeleteRow('OT', rowId);
            }
        });
    });

    lucide.createIcons();
}

// ==========================================================================
//  TAB 3: FACTURAS (RENDER & UPDATE)
// ==========================================================================
function renderInvoicesTable() {
    const tbody = document.getElementById('invoices-table-body');
    tbody.innerHTML = '';

    const invoices = allData?.data?.Facturas || [];

    if (invoices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-secondary">No hay facturas registradas.</td></tr>';
        return;
    }

    const sortedInvoices = [...invoices].sort((a, b) => {
        const valA = a.values[CODA_COLS.Facturas.fecha_emision] || '';
        const valB = b.values[CODA_COLS.Facturas.fecha_emision] || '';
        return valB.localeCompare(valA);
    });

    sortedInvoices.forEach(row => {
        const val   = row.values;
        const rowId = row.id;
        const currentEstado = val[CODA_COLS.Facturas.estado] || 'PENDIENTE';

        const monedaSymbol = val[CODA_COLS.Facturas.moneda] === 'Dolares' ? '$' : 'S/';
        const monto = parseFloat(val[CODA_COLS.Facturas.monto]) || 0;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${val[CODA_COLS.Facturas.fecha_emision] || '-'}</td>
            <td><strong>${val[CODA_COLS.Facturas.factura] || '-'}</strong></td>
            <td>${val[CODA_COLS.Facturas.cliente] || '-'}</td>
            <td class="text-right"><strong>${monedaSymbol} ${monto.toFixed(2)}</strong></td>
            <td>${val[CODA_COLS.Facturas.fecha_pago] || '-'}</td>
            <td class="text-danger text-center font-bold">${val[CODA_COLS.Facturas.atraso] || '0 d'}</td>
            <td><span class="text-secondary">${val[CODA_COLS.Facturas.ot] || '-'}</span></td>
            <td><span class="state-badge inv-${String(currentEstado).toLowerCase().replace(' ', '_')}">${currentEstado}</span></td>
            <td>
                <div class="table-actions-cell">
                    <select class="select-table-status-inv" data-rowid="${rowId}" data-prev-estado="${currentEstado}">
                        <option value="PENDIENTE"            ${currentEstado === 'PENDIENTE'            ? 'selected' : ''}>PENDIENTE</option>
                        <option value="COBRADO"              ${currentEstado === 'COBRADO'              ? 'selected' : ''}>COBRADO</option>
                        <option value="DETRACCION PENDIENTE" ${currentEstado === 'DETRACCION PENDIENTE' ? 'selected' : ''}>DETRAC. PEND.</option>
                        <option value="ANULADO"              ${currentEstado === 'ANULADO'              ? 'selected' : ''}>ANULADO</option>
                    </select>
                    <button class="btn btn-danger btn-icon-only btn-delete-inv" data-rowid="${rowId}" title="Eliminar Factura">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });

    tbody.querySelectorAll('.select-table-status-inv').forEach(select => {
        select.addEventListener('change', async () => {
            const rowId      = select.getAttribute('data-rowid');
            const prevEstado  = select.getAttribute('data-prev-estado');
            const nuevoEstado = select.value;
            const ok = await handleUpdateRow('Facturas', rowId, [{ key: 'estado', value: nuevoEstado }]);
            if (!ok) {
                select.value = prevEstado;
            } else {
                select.setAttribute('data-prev-estado', nuevoEstado);
            }
        });
    });

    tbody.querySelectorAll('.btn-delete-inv').forEach(btn => {
        btn.addEventListener('click', async () => {
            const rowId = btn.getAttribute('data-rowid');
            if (confirm('¿Estás seguro de que deseas eliminar esta Factura de Coda?')) {
                await handleDeleteRow('Facturas', rowId);
            }
        });
    });

    lucide.createIcons();
}

// ==========================================================================
//  TAB 4: GASTOS Y COMPRAS (RENDER & DELETE)
// ==========================================================================
function renderExpensesTable() {
    const tbody = document.getElementById('expenses-table-body');
    tbody.innerHTML = '';

    const expenses = allData?.data?.GasCom || [];

    if (expenses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-secondary">No hay egresos registrados.</td></tr>';
        return;
    }

    const sortedExpenses = [...expenses].sort((a, b) => {
        const valA = a.values[CODA_COLS.GasCom.fecha] || '';
        const valB = b.values[CODA_COLS.GasCom.fecha] || '';
        return valB.localeCompare(valA);
    });

    sortedExpenses.forEach(row => {
        const val   = row.values;
        const rowId = row.id;

        const monedaSymbol = val[CODA_COLS.GasCom.moneda] === 'Dolares' ? '$' : 'S/';
        const monto = parseFloat(val[CODA_COLS.GasCom.monto]) || 0;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${val[CODA_COLS.GasCom.fecha] || '-'}</td>
            <td><strong>${val[CODA_COLS.GasCom.proveedor] || '-'}</strong></td>
            <td class="text-right"><strong>${monedaSymbol} ${monto.toFixed(2)}</strong></td>
            <td><small>${val[CODA_COLS.GasCom.concepto] || '-'}</small></td>
            <td>
                <strong>${val[CODA_COLS.GasCom.categoria] || '-'}</strong><br>
                <small class="text-secondary">${val[CODA_COLS.GasCom.subcategoria] || '-'}</small>
            </td>
            <td><span class="text-secondary font-semibold">${val[CODA_COLS.GasCom.ot] || '-'}</span></td>
            <td>
                <button class="btn btn-danger btn-icon-only btn-delete-exp" data-rowid="${rowId}" title="Eliminar Gasto">
                    <i data-lucide="trash-2"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    tbody.querySelectorAll('.btn-delete-exp').forEach(btn => {
        btn.addEventListener('click', async () => {
            const rowId = btn.getAttribute('data-rowid');
            if (confirm('¿Estás seguro de que deseas eliminar este registro de Gasto de Coda?')) {
                await handleDeleteRow('GasCom', rowId);
            }
        });
    });

    lucide.createIcons();
}

// ==========================================================================
//  TAB 5: PERSONAL (RENDER & DELETE)
// ==========================================================================
function renderPersonalTable() {
    const tbody = document.getElementById('personal-table-body');
    tbody.innerHTML = '';

    const personal = allData?.data?.Personal || [];

    if (personal.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-secondary">No hay personal registrado en el taller.</td></tr>';
        return;
    }

    personal.forEach(row => {
        const val   = row.values;
        const rowId = row.id;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${val[CODA_COLS.Personal.nombre] || '-'}</strong></td>
            <td>${val[CODA_COLS.Personal.dni] || '-'}</td>
            <td><small>${val[CODA_COLS.Personal.direccion] || '-'}</small></td>
            <td>${val[CODA_COLS.Personal.celular] || '-'}</td>
            <td class="text-center">${val[CODA_COLS.Personal.edad] || '-'}</td>
            <td>${val[CODA_COLS.Personal.bcp] || '-'}</td>
            <td>${val[CODA_COLS.Personal.bbva] || '-'}</td>
            <td>
                <button class="btn btn-danger btn-icon-only btn-delete-per" data-rowid="${rowId}" title="Eliminar Ficha">
                    <i data-lucide="trash-2"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    tbody.querySelectorAll('.btn-delete-per').forEach(btn => {
        btn.addEventListener('click', async () => {
            const rowId = btn.getAttribute('data-rowid');
            if (confirm('¿Estás seguro de que deseas eliminar esta ficha de personal de Coda?')) {
                await handleDeleteRow('Personal', rowId);
            }
        });
    });

    lucide.createIcons();
}

// ==========================================================================
//  CRUD ACTIONS — Envían claves abstractas al backend (no IDs de Coda)
// ==========================================================================
/**
 * handleUpdateRow — actualiza celdas de una fila.
 * cells: [{ key: 'estado', value: 'COMPLETADO' }, ...]
 * Retorna true si OK, false si falla.
 */
async function handleUpdateRow(tableName, rowId, cells) {
    try {
        const response = await fetchProtected('/api/coda_crud.php?action=update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ table: tableName, row_id: rowId, cells })
        });
        if (!response) return false; // Redirigido a login

        const res = await response.json();
        if (response.ok && res.success) {
            fetchData(); // Recargar datos en silencio
            return true;
        } else {
            console.error('Error actualizar Coda:', res.error);
            alert('Error al actualizar registro en Coda: ' + (res.error || 'Intenta de nuevo.'));
            return false;
        }
    } catch (err) {
        console.error('Error de red al actualizar Coda:', err);
        return false;
    }
}

/**
 * handleDeleteRow — elimina una fila de Coda.
 */
async function handleDeleteRow(tableName, rowId) {
    try {
        const response = await fetchProtected('/api/coda_crud.php?action=delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ table: tableName, row_id: rowId })
        });
        if (!response) return;

        const res = await response.json();
        if (response.ok && res.success) {
            fetchData();
        } else {
            alert('Error al eliminar registro de Coda: ' + (res.error || 'Intenta de nuevo.'));
        }
    } catch (err) {
        console.error('Error de red al eliminar en Coda:', err);
    }
}

// ==========================================================================
//  FORMULARIOS SUBMISSIONS (CREATE ROW)
// ==========================================================================
function setupFormSubmissions() {
    // 1. FORMULARIO OT
    document.getElementById('form-ot').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btn-submit-ot');
        btn.disabled = true;
        btn.innerText = 'Registrando en Coda...';

        const codigo  = document.getElementById('ot-code').value.trim();
        const cliente = document.getElementById('ot-client').value.trim();
        const precio  = parseFloat(document.getElementById('ot-price').value);

        if (!codigo) { alert('El código de OT no puede estar vacío.'); btn.disabled = false; btn.innerText = 'Registrar OT en Coda'; return; }
        if (!cliente) { alert('El cliente no puede estar vacío.'); btn.disabled = false; btn.innerText = 'Registrar OT en Coda'; return; }
        if (isNaN(precio) || precio < 0) { alert('Ingresa un precio de venta válido (número >= 0).'); btn.disabled = false; btn.innerText = 'Registrar OT en Coda'; return; }

        const cells = [
            { key: 'codigo',       value: codigo },
            { key: 'cliente',      value: cliente },
            { key: 'precio_venta', value: precio },
            { key: 'estado',       value: document.getElementById('ot-status').value }
        ];

        const dateVal    = document.getElementById('ot-date').value;
        if (dateVal) cells.push({ key: 'fecha_inicio', value: dateVal });

        const deliveryVal = document.getElementById('ot-delivery').value;
        if (deliveryVal) cells.push({ key: 'fecha_entrega', value: deliveryVal });

        const descVal = document.getElementById('ot-desc').value.trim();
        if (descVal) cells.push({ key: 'descripcion', value: descVal });

        const success = await handleAddRow('OT', cells);
        if (success) {
            document.getElementById('form-ot').reset();
            document.getElementById('form-ot-card').classList.add('hidden');
        }
        btn.disabled = false;
        btn.innerText = 'Registrar OT en Coda';
    });

    // 2. FORMULARIO FACTURA
    document.getElementById('form-invoice').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btn-submit-invoice');
        btn.disabled = true;
        btn.innerText = 'Registrando...';

        const factura = document.getElementById('inv-code').value.trim();
        const cliente = document.getElementById('inv-client').value.trim();
        const monto   = parseFloat(document.getElementById('inv-amount').value);

        if (!factura) { alert('El código de factura no puede estar vacío.'); btn.disabled = false; btn.innerText = 'Registrar Factura en Coda'; return; }
        if (!cliente) { alert('El cliente no puede estar vacío.'); btn.disabled = false; btn.innerText = 'Registrar Factura en Coda'; return; }
        if (isNaN(monto) || monto <= 0) { alert('Ingresa un monto válido y mayor a cero.'); btn.disabled = false; btn.innerText = 'Registrar Factura en Coda'; return; }

        const cells = [
            { key: 'factura', value: factura },
            { key: 'cliente', value: cliente },
            { key: 'monto',   value: monto },
            { key: 'moneda',  value: document.getElementById('inv-currency').value },
            { key: 'estado',  value: document.getElementById('inv-status').value }
        ];

        const dateEmi = document.getElementById('inv-date-emision').value;
        if (dateEmi) cells.push({ key: 'fecha_emision', value: dateEmi });

        const datePago = document.getElementById('inv-date-pago').value;
        if (datePago) cells.push({ key: 'fecha_pago', value: datePago });

        const otVal = document.getElementById('inv-ot').value;
        if (otVal) cells.push({ key: 'ot', value: otVal });

        const success = await handleAddRow('Facturas', cells);
        if (success) {
            document.getElementById('form-invoice').reset();
            document.getElementById('form-invoice-card').classList.add('hidden');
        }
        btn.disabled = false;
        btn.innerText = 'Registrar Factura en Coda';
    });

    // 3. FORMULARIO GASTOS (GASCOM)
    document.getElementById('form-expense').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btn-submit-expense');
        btn.disabled = true;
        btn.innerText = 'Registrando...';

        const fecha      = document.getElementById('exp-date').value;
        const proveedor  = document.getElementById('exp-provider').value.trim();
        const monto      = parseFloat(document.getElementById('exp-amount').value);
        const concepto   = document.getElementById('exp-desc').value.trim();

        if (!fecha) { alert('Selecciona una fecha.'); btn.disabled = false; btn.innerText = 'Registrar Egreso en Coda'; return; }
        if (!proveedor) { alert('El proveedor no puede estar vacío.'); btn.disabled = false; btn.innerText = 'Registrar Egreso en Coda'; return; }
        if (isNaN(monto) || monto <= 0) { alert('Ingresa un monto válido y mayor a cero.'); btn.disabled = false; btn.innerText = 'Registrar Egreso en Coda'; return; }
        if (!concepto) { alert('El concepto no puede estar vacío.'); btn.disabled = false; btn.innerText = 'Registrar Egreso en Coda'; return; }

        const cells = [
            { key: 'fecha',      value: fecha },
            { key: 'proveedor',  value: proveedor },
            { key: 'monto',      value: monto },
            { key: 'moneda',     value: document.getElementById('exp-currency').value },
            { key: 'categoria',  value: document.getElementById('exp-category').value },
            { key: 'concepto',   value: concepto },
            { key: 'cantidad',   value: 1 }
        ];

        const otVal = document.getElementById('exp-ot').value;
        if (otVal) cells.push({ key: 'ot', value: otVal });

        const success = await handleAddRow('GasCom', cells);
        if (success) {
            document.getElementById('form-expense').reset();
            document.getElementById('form-expense-card').classList.add('hidden');
        }
        btn.disabled = false;
        btn.innerText = 'Registrar Egreso en Coda';
    });

    // 4. FORMULARIO TRABAJADOR
    document.getElementById('form-personal').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btn-submit-personal');
        btn.disabled = true;
        btn.innerText = 'Registrando...';

        const nombre = document.getElementById('per-name').value.trim();
        const dniRaw = document.getElementById('per-dni').value.trim();

        if (!nombre) { alert('El nombre no puede estar vacío.'); btn.disabled = false; btn.innerText = 'Registrar Ficha en Coda'; return; }
        if (!dniRaw || !/^\d{8}$/.test(dniRaw)) { alert('El DNI debe tener exactamente 8 dígitos numéricos.'); btn.disabled = false; btn.innerText = 'Registrar Ficha en Coda'; return; }

        const cells = [
            { key: 'nombre', value: nombre },
            { key: 'dni',    value: dniRaw }
        ];

        const phone = document.getElementById('per-phone').value.trim();
        if (phone) cells.push({ key: 'celular', value: phone });

        const ageRaw = document.getElementById('per-age').value;
        if (ageRaw) {
            const age = parseInt(ageRaw);
            if (isNaN(age) || age < 14 || age > 80) {
                alert('Ingresa una edad válida (entre 14 y 80 años).');
                btn.disabled = false; btn.innerText = 'Registrar Ficha en Coda'; return;
            }
            cells.push({ key: 'edad', value: age });
        }

        const address = document.getElementById('per-address').value.trim();
        if (address) cells.push({ key: 'direccion', value: address });

        const bcp = document.getElementById('per-bcp').value.trim();
        if (bcp) cells.push({ key: 'bcp', value: bcp });

        const bbva = document.getElementById('per-bbva').value.trim();
        if (bbva) cells.push({ key: 'bbva', value: bbva });

        const success = await handleAddRow('Personal', cells);
        if (success) {
            document.getElementById('form-personal').reset();
            document.getElementById('form-personal-card').classList.add('hidden');
        }
        btn.disabled = false;
        btn.innerText = 'Registrar Ficha en Coda';
    });
}

async function handleAddRow(tableName, cells) {
    try {
        const response = await fetchProtected('/api/coda_crud.php?action=add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ table: tableName, cells })
        });
        if (!response) return false;

        const res = await response.json();
        if (response.ok && res.success) {
            await fetchData();
            return true;
        } else {
            alert('Error al registrar en Coda: ' + (res.error || 'Verifica e intenta de nuevo.'));
            return false;
        }
    } catch (err) {
        console.error('Error de red al añadir fila a Coda:', err);
        alert('Error de red al registrar en Coda.');
        return false;
    }
}

// ==========================================================================
//  SINCRONIZACIÓN DE GMAIL (SSE TERMINAL MODAL)
// ==========================================================================
function setupSync() {
    const btnSync       = document.getElementById('btn-sync-emails');
    const modal         = document.getElementById('modal-sync');
    const btnClose      = document.getElementById('btn-close-modal');
    const consoleOutput = document.getElementById('console-output');
    const spinner       = document.getElementById('modal-spinner');

    if (!btnSync) return;

    btnSync.addEventListener('click', () => {
        modal.classList.remove('hidden');
        btnClose.disabled = true;
        spinner.classList.remove('hidden');
        consoleOutput.innerHTML = '';
        appendConsoleLine('Iniciando canal de comunicación en vivo...', 'system');

        const serverStatus     = document.getElementById('server-status');
        const serverStatusText = document.getElementById('server-status-text');
        serverStatus.className = 'status-indicator loading';
        serverStatusText.innerText = 'Sincronizando...';

        const eventSource = API_BASE_URL 
            ? new EventSource(API_BASE_URL + '/api/sync.php', { withCredentials: true }) 
            : new EventSource('/api/sync.php');

        eventSource.onmessage = (event) => {
            const line = event.data;
            let lineClass = '';

            if (line.startsWith('[START]'))       lineClass = 'system';
            else if (line.startsWith('[DONE]')) {
                lineClass = 'success';
                eventSource.close();
                btnClose.disabled = false;
                spinner.classList.add('hidden');
                serverStatus.className = 'status-indicator online';
                serverStatusText.innerText = 'Coda Cloud Online';
                fetchData();
            } else if (line.startsWith('[ERROR]') || line.includes('ERROR') || line.includes('FATAL')) {
                lineClass = 'error';
            } else if (line.includes('COMPLETADO') || line.includes('CODA OK') || line.includes('OK')) {
                lineClass = 'success';
            } else if (line.includes('[!]') || line.includes('Warning')) {
                lineClass = 'warn';
            }

            appendConsoleLine(line, lineClass);
        };

        eventSource.onerror = (err) => {
            console.error('SSE Error:', err);
            appendConsoleLine('Error de conexión con el script de sincronización.', 'error');
            eventSource.close();
            btnClose.disabled = false;
            spinner.classList.add('hidden');
            serverStatus.className = 'status-indicator online';
            serverStatusText.innerText = 'Coda Cloud Online';
        };
    });

    btnClose.addEventListener('click', () => modal.classList.add('hidden'));
}

function appendConsoleLine(text, className = '') {
    const consoleOutput = document.getElementById('console-output');
    if (!consoleOutput) return;
    const div = document.createElement('div');
    div.className = `console-line ${className}`;
    div.innerText = text;
    consoleOutput.appendChild(div);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

// ==========================================================================
//  HELPERS (Formateo de moneda, logout)
// ==========================================================================
function formatCurrency(monto, moneda) {
    const cleanMoneda = moneda ? moneda.toLowerCase() : 'soles';
    if (cleanMoneda === 'dolares' || cleanMoneda === 'dólares') {
        return `$ ${parseFloat(monto).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    } else {
        return `S/ ${parseFloat(monto).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
}

async function handleLogout() {
    if (!confirm('¿Estás seguro de que deseas cerrar sesión?')) return;
    try {
        const response = await fetchProtected('/api/logout.php', { method: 'POST' });
        if (response.ok) {
            window.location.href = '/login.html';
        } else {
            alert('Error al cerrar la sesión.');
        }
    } catch (err) {
        console.error('Error al cerrar sesión:', err);
        window.location.href = '/login.html';
    }
}

// ==========================================================================
//  CHATBOT DE INTELIGENCIA ARTIFICIAL (GEMINI INTEGRATION)
// ==========================================================================
function setupAIChat() {
    const bubble = document.getElementById('ai-chat-bubble');
    const windowChat = document.getElementById('ai-chat-window');
    const btnClose = document.getElementById('btn-chat-close');
    const chatInput = document.getElementById('chat-input');
    const btnSend = document.getElementById('btn-chat-send');
    const chatMessages = document.getElementById('chat-messages');

    if (!bubble || !windowChat) return;

    // Toggle ventana de chat
    bubble.addEventListener('click', () => {
        windowChat.classList.toggle('hidden');
        if (!windowChat.classList.contains('hidden')) {
            chatInput.focus();
            scrollChatToBottom();
        }
    });

    btnClose.addEventListener('click', () => {
        windowChat.classList.add('hidden');
    });

    // Enviar mensaje al hacer click o presionar Enter
    btnSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // Limpiar input y agregar mensaje del usuario
        chatInput.value = '';
        appendMessage('user', text);
        scrollChatToBottom();

        // Agregar indicador de "escribiendo..."
        const typingId = appendTypingIndicator();
        scrollChatToBottom();

        // Bloquear controles temporalmente
        chatInput.disabled = true;
        btnSend.disabled = true;

        try {
            const response = await fetchProtected('/api/chat.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            removeTypingIndicator(typingId);

            if (!response) {
                // Redirigido a login
                return;
            }

            const data = await response.json();
            if (response.ok && data.success) {
                appendMessage('bot', data.response);
            } else {
                appendMessage('bot', 'Error: ' + (data.error || 'No se pudo conectar con el asistente.'));
            }
        } catch (err) {
            removeTypingIndicator(typingId);
            console.error('Error en chat:', err);
            appendMessage('bot', 'Error de red. Por favor verifica tu conexión.');
        } finally {
            chatInput.disabled = false;
            btnSend.disabled = false;
            chatInput.focus();
            scrollChatToBottom();
        }
    }

    function appendMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-msg ${sender}`;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'msg-bubble';
        
        if (sender === 'bot') {
            bubbleDiv.innerHTML = formatMarkdown(text);
        } else {
            bubbleDiv.textContent = text;
        }
        
        msgDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(msgDiv);
    }

    function appendTypingIndicator() {
        const id = 'typing_' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-msg bot';
        msgDiv.id = id;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'msg-bubble';
        bubbleDiv.innerHTML = '<span style="opacity: 0.6; font-style: italic;">Inprometal AI está analizando los datos...</span>';
        
        msgDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(msgDiv);
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollChatToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatMarkdown(text) {
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
            
        // Negritas
        html = html.replace(/\*\*(.*?)\*\//g, '<strong>$1</strong>');
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Procesar líneas para listas y tablas
        const lines = html.split('\n');
        let inList = false;
        let inTable = false;
        let formattedLines = [];
        let tableRows = [];
        
        for (let i = 0; i < lines.length; i++) {
            let line = lines[i].trim();
            
            if (line.startsWith('|')) {
                if (inList) {
                    formattedLines.push('</ul>');
                    inList = false;
                }
                if (!inTable) {
                    inTable = true;
                    tableRows = [];
                }
                if (line.match(/^\|[\s:-|]*\|$/)) {
                    continue;
                }
                let cells = line.split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
                tableRows.push(cells);
            } else {
                if (inTable) {
                    let tableHtml = '<table>';
                    tableRows.forEach((row, rIdx) => {
                        tableHtml += '<tr>';
                        row.forEach(cell => {
                            let tag = (rIdx === 0) ? 'th' : 'td';
                            tableHtml += `<${tag}>${cell}</${tag}>`;
                        });
                        tableHtml += '</tr>';
                    });
                    tableHtml += '</table>';
                    formattedLines.push(tableHtml);
                    inTable = false;
                }
                
                if (line.startsWith('- ') || line.startsWith('* ')) {
                    if (!inList) {
                        formattedLines.push('<ul>');
                        inList = true;
                    }
                    formattedLines.push('<li>' + line.substring(2) + '</li>');
                } else {
                    if (inList) {
                        formattedLines.push('</ul>');
                        inList = false;
                    }
                    formattedLines.push(lines[i]);
                }
            }
        }
        
        if (inTable) {
            let tableHtml = '<table>';
            tableRows.forEach((row, rIdx) => {
                tableHtml += '<tr>';
                row.forEach(cell => {
                    let tag = (rIdx === 0) ? 'th' : 'td';
                    tableHtml += `<${tag}>${cell}</${tag}>`;
                });
                tableHtml += '</tr>';
            });
            tableHtml += '</table>';
            formattedLines.push(tableHtml);
        }
        if (inList) {
            formattedLines.push('</ul>');
        }
        
        html = formattedLines.join('\n');
        html = html.replace(/\n/g, '<br>');
        html = html.replace(/<\/table><br>/g, '</table>');
        html = html.replace(/<\/ul><br>/g, '</ul>');
        
        return html;
    }
}

