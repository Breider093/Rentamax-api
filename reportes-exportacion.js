(function () {
    function abrirExportacion(tipoReporte, tipoArchivo, filtros) {
        const rutas = {
            inventario: {
                pdf: '/api/reportes/inventario/exportar-pdf/',
                excel: '/api/reportes/inventario/exportar-excel/',
            },
            'equipos-obra': {
                pdf: '/api/reportes/equipos-obra/exportar-pdf/',
                excel: '/api/reportes/equipos-obra/exportar-excel/',
            },
        };

        const baseUrl = rutas[tipoReporte] && rutas[tipoReporte][tipoArchivo];
        if (!baseUrl) {
            throw new Error('Tipo de reporte o archivo no soportado.');
        }

        const params = new URLSearchParams();
        Object.entries(filtros || {}).forEach(([nombre, valor]) => {
            if (valor !== undefined && valor !== null && valor !== '') {
                params.set(nombre, valor);
            }
        });

        const query = params.toString();
        window.open(query ? `${baseUrl}?${query}` : baseUrl, '_blank');
    }

    window.abrirExportacion = abrirExportacion;
}());