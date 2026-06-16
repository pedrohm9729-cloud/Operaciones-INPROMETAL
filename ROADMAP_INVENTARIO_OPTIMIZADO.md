# 🚀 ROADMAP OPTIMIZADO - OPERACIONES INPROMETAL PARA GERENTE GENERAL (ÚNICO USUARIO)

**Perfil:** Gerente General (único usuario)  
**Sin Workflow** ✅ (solo tú acceso)  
**CON Inventario** 🔴 (HIGH PRIORITY)  
**Objetivo:** Sistema completo en 2-3 meses

---

## 📋 REQUERIMIENTOS CONFIRMADOS

### ✅ MANTENER
- Dashboard KPI (resumen operativo)
- Órdenes de Trabajo (OT)
- Facturas y Cobros
- Gastos Comerciales
- Personal Taller
- Chat IA (Gemini análisis)
- Sincronización Gmail

### ❌ REMOVER
- Workflow de aprobación (tú solo decidirás)
- Multi-usuario auth (solo admin)

### 🔴 AGREGAR (HIGH PRIORITY)
- **Inventario Management** ← NUEVA PRIORIDAD

---

## 🎯 ROADMAP PRIORIZADO

### FASE 1: CORE INVENTORY (3 semanas) - CRÍTICO

**Objetivo:** Sistema de inventario funcional para taller metalworking

#### 1.1 Módulo Inventario Básico
```
Tabla: Inventario
├─ Código SKU (ej: AC-001)
├─ Descripción (ej: Acero inoxidable 200kg)
├─ Categoría (Fierros, Consumibles, Herramientas, etc)
├─ Unidad de medida (kg, m, unidad, etc)
├─ Stock actual
├─ Stock mínimo (reorder point)
├─ Stock máximo
├─ Ubicación en taller
├─ Costo unitario
├─ Fecha entrada
├─ Proveedor
├─ Estado (Activo, Inactivo, Descontinuado)
└─ Notas

CRUD:
✅ Crear artículo (nuevo material)
✅ Editar artículo (actualizar stock, ubicación)
✅ Eliminar artículo (marcar inactivo)
✅ Ver listado (tabla con filtros)
```

**Tablas Coda necesarias:**
- Inventario (maestro)
- Categorías (dropdown)
- Proveedores (dropdown)

**Tiempo:** 1.5 semanas  
**Esfuerzo:** 20 horas

#### 1.2 Movimientos de Inventario
```
Tabla: Movimientos Inventario
├─ Fecha movimiento
├─ Tipo: Entrada, Salida, Ajuste, Devolución
├─ Artículo (link a Inventario)
├─ Cantidad
├─ Referencia (OT, Factura, Compra, Manual)
├─ Notas (por qué se movió)
├─ Usuario (siempre tú)
└─ Timestamp

TRANSACCIONES:
✅ Entrada por compra (aumentar stock)
✅ Salida por OT (disminuir stock)
✅ Ajuste manual (corrección)
✅ Devolución a proveedor
```

**Tiempo:** 1 semana  
**Esfuerzo:** 12 horas

#### 1.3 Dashboard Inventario
```
KPIs Visuales:
├─ Stock Total Valor (en Soles)
├─ Artículos Bajo Stock (< mínimo)
├─ Rotación promedio (meses sin movimiento)
├─ Artículos en Obsolescencia (>12 meses sin mover)
├─ Proveedor Top 3
└─ Categoría más usada (gráfico)

Alertas Visuales:
├─ 🔴 ROJO: Artículo sin stock, necesario para OT en progress
├─ 🟠 NARANJA: Stock bajo mínimo, ordenar pronto
├─ 🟡 AMARILLO: Stock en límite máximo, reducir compras
└─ 🟢 VERDE: Stock óptimo

Acciones desde Dashboard:
✅ Click → Ver movimientos del artículo
✅ Click → Link a OT que usa este material
✅ Click → Link a facturas de proveedores
```

**Tiempo:** 1.5 semanas  
**Esfuerzo:** 15 horas

---

### FASE 2: INTEGRACIÓN OT ↔ INVENTARIO (2 semanas)

#### 2.1 Consumo Automático en OT
```
Cuando creas OT y especificas materiales:

Formulario OT:
├─ ... datos actuales ...
└─ [NUEVO] Materiales Utilizados
   ├─ Artículo: [Dropdown Inventario]
   ├─ Cantidad: [Input]
   └─ Agregar otro material

Acción al completar OT:
✅ Sistema REST automáticamente consume del inventario
   Ejemplo: OT usa 5kg de Acero
   → Inventario: Acero = Stock anterior - 5kg
   → Crea movimiento: Salida por OT-2026-0001

Reversión si cancela OT:
✅ Si cancelas OT → Stock se devuelve
```

**Tiempo:** 1 semana  
**Esfuerzo:** 10 horas

#### 2.2 Reservas Preventivas
```
Cuando planificas OT en futuro:

Estado OT "PLANIFICADO":
✅ Reserva el stock (no lo consume aún)
✅ Dashboard muestra: "Stock real" vs "Stock disponible"
   Ejemplo: Acero = 100kg real, 95kg disponible
   (5kg reservados para OT próxima)

Estado OT "EN EJECUCIÓN":
✅ Consume las reservas → Stock real baja

Estado OT "COMPLETADO":
✅ Confirmación de consumo
```

**Tiempo:** 1 semana  
**Esfuerzo:** 8 horas

---

### FASE 3: COMPRAS & REORDEN (2 semanas)

#### 3.1 Órdenes de Compra
```
Nueva Tabla: Órdenes de Compra (PO)
├─ Número PO (Auto-generado: PO-2026-0001)
├─ Proveedor (link)
├─ Fecha PO
├─ Fecha entrega esperada
├─ Estado: Borrador, Enviada, Confirmada, Recibida, Cancelada
├─ Artículos:
│  ├─ Artículo (link Inventario)
│  ├─ Cantidad
│  ├─ Precio unitario
│  ├─ Subtotal
│  └─ Descripción especial
├─ Total
└─ Notas

FLUJO:
✅ Crear PO cuando stock baja del mínimo
✅ Rastrear estado: enviada → confirmada → recibida
✅ Al recibir → Actualiza automáticamente Inventario
```

**Tiempo:** 1 semana  
**Esfuerzo:** 12 horas

#### 3.2 Auto-Alert de Reorden
```
Sistema de Alertas:
├─ Cada noche (cron job):
│  ├─ Verifica todos los artículos
│  ├─ Si Stock < Mínimo → ALERTA
│  ├─ Genera sugerencia de compra
│  └─ Envía email al gerente (tú)
│
└─ Sugerencia include:
   ├─ Qué comprar (artículo)
   ├─ Cuánto (hasta stock máximo)
   ├─ De quién (proveedor preferido)
   └─ Link para crear PO directamente
```

**Tiempo:** 1 semana  
**Esfuerzo:** 8 horas

---

### FASE 4: ALERTS + FORECASTING (2 semanas)

#### 4.1 Sistema de Alertas Integrado
```
Alertas para Gerente General (por email/dashboard):

🔴 CRÍTICO:
├─ Artículo agotado pero OT necesita (falta para producción)
├─ PO vencida (debe haber llegado hace 5 días)
├─ Stock en negativo (error de entrada)

🟠 IMPORTANTE:
├─ Stock bajo mínimo (3 artículos hoy)
├─ Artículo próximo a vencer (medicinas, adhesivos)
├─ Rotación baja (no se movió en 6 meses)

🟡 INFO:
├─ PO confirmada (llegará mañana)
├─ Inventario recibido (PO completada)
├─ Ajuste manual registrado
```

**Tiempo:** 1 semana  
**Esfuerzo:** 10 horas

#### 4.2 Forecasting de Consumo
```
Dashboard Predictivo:
├─ Consumo semanal (histórico 8 semanas)
├─ Tendencia: ↑ aumentando, ↓ disminuyendo, → estable
├─ Proyección: "En 10 días necesitarás comprar Acero"
├─ Lead time: "Proveedor tarda 7 días"
└─ Recomendación: "Compra hoy para no quedarte sin stock"

Artículo by artículo:
├─ Acero: 50kg/semana, próximo reorden 2026-06-23
├─ Consumibles: 20 unidades/semana, próximo reorden 2026-06-25
└─ Herramientas: 2 unidades/mes, próximo reorden 2026-07-15
```

**Tiempo:** 1 semana  
**Esfuerzo:** 12 horas

---

### FASE 5: REPORTES + AUDIT (1 semana)

#### 5.1 Reportes Inventario
```
Reportes disponibles (PDF/CSV):

Reporte 1: Valuación de Inventario
├─ Total stock actual valor (S/.)
├─ Por categoría (Fierros, Consumibles, etc)
├─ Por proveedor
└─ Gráfico pie

Reporte 2: Movimientos (período)
├─ Todas las entradas/salidas en rango
├─ Por tipo (entrada, salida, ajuste)
├─ Consumo por OT
└─ Tabla detallada

Reporte 3: Rotación
├─ Artículos sin movimiento >6 meses
├─ Candidatos a obsolescencia
├─ Valor bloqueado en stock muerto

Reporte 4: Compras
├─ Todas las PO en rango
├─ Por proveedor
├─ Gasto total compras
├─ Lead time promedio
```

**Tiempo:** 1 semana  
**Esfuerzo:** 10 horas

#### 5.2 Audit Trail Inventario
```
Quién hizo qué cuándo:
├─ Creó artículo: 2026-06-14 09:30 (Gerente General)
├─ Editó stock: 2026-06-14 14:00 (entrada PO-123)
├─ Creó movimiento: 2026-06-14 15:30 (salida OT-0025)
├─ Ajuste manual: 2026-06-14 16:00 (nota: error entrada)
└─ Historial completo con antes/después de valores
```

**Tiempo:** Incluido en código anterior  
**Esfuerzo:** 2 horas

---

## 📊 RESUMEN ROADMAP

| Fase | Descripción | Semanas | Horas | Features |
|------|-------------|---------|-------|----------|
| 1 | Inventario Core | 3 | 50 | Maestro, Movimientos, Dashboard |
| 2 | Integración OT | 2 | 18 | Consumo, Reservas |
| 3 | Compras | 2 | 20 | PO, Auto-alert |
| 4 | Alertas + Forecast | 2 | 22 | Notificaciones, Predicción |
| 5 | Reportes + Audit | 1 | 10 | PDFs, Trail |
| **TOTAL** | **Sistema Completo** | **10 semanas** | **120 horas** | **Inventario Pro** |

---

## 💰 ESTIMACIÓN COSTO

### Opción A: Desarrollo Externo
```
120 horas × $150/hora = $18,000
+ Testing + deployment + training = $2,000
TOTAL: $20,000 USD (~$75,000 PEN)

Timeframe: 10 semanas (2.5 meses)
Equipo: 1 full-stack developer
```

### Opción B: Desarrollo Interno (si tienes developer)
```
120 horas ~ 3 sprints de 2 semanas
Recursos: 1 developer
Costo: Tu salario developer
+ Cloud/hosting: $50-100/mes
```

### Opción C: Combinado (Recomendado)
```
Tú + Developer freelance:
- Tú: Especificaciones, testing, decisiones
- Developer: 80 horas ($12K)
- Formación: 20 horas ($1K)
TOTAL: $13,000 USD

Timeframe: 3 meses (más flexible)
```

---

## 🎯 PRIORIDAD ABSOLUTA

### SEM 1-3: INVENTARIO BASE
```
✅ MUST HAVE:
├─ Tabla Inventario (SKU, stock, precio)
├─ Movimientos (entrada/salida)
├─ Dashboard con KPI stock
└─ Alertas visuales (rojo/amarillo/verde)

⏸️ NICE TO HAVE (postergar):
└─ Forecast (puede agregarse en Fase 4)
```

**Por qué:** Sin inventario, no ves qué tienes para OTs.

### SEM 4-5: INTEGRACIÓN OT
```
✅ MUST HAVE:
├─ OT consume inventario automático
├─ Reservas preventivas
└─ Stock disponible vs Stock real

⏸️ NICE TO HAVE:
└─ Historial detallado
```

**Por qué:** OT es lo más importante. Debe integrar con inventario.

### SEM 6-7: COMPRAS
```
✅ MUST HAVE:
├─ Órdenes de Compra (PO)
├─ Auto-alert reorden
└─ Recepción PO

⏸️ NICE TO HAVE:
└─ Email notificaciones
```

**Por qué:** Reorden automático = no te quedas sin stock.

### SEM 8-10: REPORTES + ALERT
```
⏸️ CAN DEFER:
├─ Reportes avanzados
├─ Forecast exacto
└─ Audit detallado
```

**Por qué:** Features de "nice to have". Después puedes agregar.

---

## 🚀 QUICK WIN: MVP EN 2 SEMANAS

Si quieres **MVP funcional rápido**:

### Semana 1
- Tabla Inventario en Coda
- CRUD básico en app.js
- Dashboard con KPI simples

### Semana 2
- Movimientos (entrada/salida)
- Integración OT consume stock
- Alertas visuales (rojo/amarillo)

**Resultado:** Sistema mínimo funcional para empezar a usar.

**Después:** Agregar compras, forecast, reportes en fases siguientes.

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### Arquitectura (Backend)
```
[ ] Crear tablas Coda:
    [ ] Inventario
    [ ] Movimientos Inventario
    [ ] Órdenes de Compra
    [ ] Categorías (dropdown)
    [ ] Proveedores (dropdown)

[ ] Endpoints PHP nuevos:
    [ ] POST /api/inventory/create
    [ ] POST /api/inventory/update
    [ ] POST /api/inventory/move
    [ ] GET /api/inventory/list
    [ ] GET /api/inventory/alerts
    [ ] POST /api/purchase-order/create

[ ] Funciones Python:
    [ ] forecast_reorder() - cron diaria
    [ ] check_low_stock() - alertas
    [ ] update_from_po() - recepción
```

### Frontend (JavaScript)
```
[ ] New Tabs:
    [ ] btn-tab-inventory
    [ ] btn-tab-purchase-orders

[ ] Functions:
    [ ] renderInventoryDashboard()
    [ ] renderInventoryTable()
    [ ] renderPurchaseOrders()
    [ ] handleCreateInventoryItem()
    [ ] handleInventoryMove()
    [ ] handleCreatePO()

[ ] Data Flow:
    [ ] allData.Inventory
    [ ] allData.Movements
    [ ] allData.PurchaseOrders
```

### Database (Coda)
```
[ ] Tabla: Inventario
    Fields: SKU, Descripción, Categoría, Stock, Mínimo, Máximo, Costo, etc

[ ] Tabla: Movimientos Inventario
    Fields: Fecha, Tipo, Artículo, Cantidad, Referencia, Notas

[ ] Tabla: Órdenes de Compra
    Fields: Número PO, Proveedor, Artículos, Total, Estado

[ ] Links:
    [ ] OT → Movimientos (consumo)
    [ ] Facturas → Inventario (materiales)
    [ ] PO → Movimientos (recepción)
```

---

## ✅ PRÓXIMOS PASOS

### INMEDIATO (Hoy)
1. ✅ Revisar este roadmap
2. [ ] Decidir si Opción A, B o C (costo/tiempo)
3. [ ] Confirmar prioridades (¿MVP 2 sem o completo 10 sem?)

### SEMANA 1
4. [ ] Crear tablas en Coda
5. [ ] Especificar campos exactos
6. [ ] Contratar developer (si aplica)
7. [ ] Empezar Fase 1

### SEMANA 2-3
8. [ ] MVP Inventario funcional
9. [ ] Testing inicial
10. [ ] Go-live Phase 1

---

## 📞 RESUMEN PARA GERENTE GENERAL

**Tu nueva plataforma tendrá:**
- ✅ Dashboard operativo actual (OT, Facturas, Gastos)
- 🆕 **Sistema de Inventario pro** (lo que pediste)
- 🆕 Alertas automáticas (stock bajo, OT próximas)
- 🆕 Forecasting (cuándo comprar)
- 🆕 Reportes (valuación, rotación)
- 🆕 Audit trail (quién hizo qué)

**Sin:**
- ❌ Workflow aprobación (solo tú decides)
- ✅ Será 85%+ de lo que necesitas para dirigir la empresa

**Tiempo:** 2-3 meses (MVP en 2 semanas)  
**Costo:** $13K-20K USD

---

**¿Listo para empezar? Confirma:**
1. ¿Empezamos con MVP 2 semanas o versión completa 10 semanas?
2. ¿Opción A (developer externo), B (tu developer) o C (combinado)?
3. ¿Alguna otra funcionalidad en inventario que necesites?

