import { Injectable } from '@angular/core';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

@Injectable({
  providedIn: 'root'
})
export class PdfService {

  private agregarEncabezado(doc: jsPDF, nombreArchivo: string) {
    const fecha = new Date().toLocaleDateString('es-MX');
    doc.setFontSize(14);
    doc.setTextColor(79, 70, 229);
    doc.text(nombreArchivo, 14, 15);
    doc.setFontSize(9);
    doc.setTextColor(150);
    doc.text(`Generado: ${fecha}`, 14, 22);
  }

  generarTablaSimple(headers: string[], filas: any[][], nombreArchivo: string) {
    const doc = new jsPDF('portrait', 'mm', 'a4');
    this.agregarEncabezado(doc, nombreArchivo);

    autoTable(doc, {
      head: [headers],
      body: filas,
      startY: 28,
      styles: { fontSize: 8 },
      headStyles: { fillColor: [79, 70, 229] },
    });

    doc.save(`${nombreArchivo}_simple.pdf`);
  }

  generarTablaHorizontal(headers: string[], filas: any[][], nombreArchivo: string) {
    const doc = new jsPDF('landscape', 'mm', 'a4');
    this.agregarEncabezado(doc, nombreArchivo);

    autoTable(doc, {
      head: [headers],
      body: filas,
      startY: 28,
      styles: { fontSize: 8 },
      headStyles: { fillColor: [79, 70, 229] },
    });

    doc.save(`${nombreArchivo}_horizontal.pdf`);
  }

  generarTablaAgrupada(headers: string[], filas: any[][], nombreArchivo: string) {
    const doc = new jsPDF('portrait', 'mm', 'a4');
    this.agregarEncabezado(doc, nombreArchivo);

    // Agrupa por el valor de la primera columna
    const grupos: { [key: string]: any[][] } = {};
    filas.forEach(fila => {
      const clave = fila[0] ?? 'Sin grupo';
      if (!grupos[clave]) grupos[clave] = [];
      grupos[clave].push(fila);
    });

    let startY = 28;
    Object.entries(grupos).forEach(([grupo, filaGrupo]) => {
      doc.setFontSize(10);
      doc.setTextColor(79, 70, 229);
      doc.text(`${grupo}`, 14, startY);

      autoTable(doc, {
        head: [headers],
        body: filaGrupo,
        startY: startY + 4,
        styles: { fontSize: 8 },
        headStyles: { fillColor: [79, 70, 229] },
        didDrawPage: (data) => { startY = data.cursor?.y ?? startY; }
      });

      startY = (doc as any).lastAutoTable.finalY + 8;
    });

    doc.save(`${nombreArchivo}_agrupado.pdf`);
  }
}