import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import * as XLSX from 'xlsx';
import { ApiService } from '../services/api';
import { ArchivoTempService } from '../services/archivo-temp.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class Dashboard {
  headers: string[] = [];
  filas: any[][] = [];
  archivoNombre = '';
  archivoOriginal: File | null = null;
  cargando = false;
  generandoPdf = false;

  constructor(
    private apiService: ApiService,
    private cdr: ChangeDetectorRef,
    private router: Router,
    private archivoTemp: ArchivoTempService
  ) {}

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;

    const archivo = input.files[0];
    this.archivoOriginal = archivo;
    this.archivoNombre = archivo.name.replace(/\.[^/.]+$/, '');
    this.headers = [];
    this.filas = [];
    this.cargando = true;
    this.cdr.detectChanges();
    this.archivoTemp.archivo = archivo;

    const reader = new FileReader();
    reader.onload = (e) => {
    const data = new Uint8Array(e.target!.result as ArrayBuffer);
    const workbook = XLSX.read(data, { type: 'array' });
    const primeraHoja = workbook.SheetNames[0];
    const hoja = workbook.Sheets[primeraHoja];

    const rango = XLSX.utils.decode_range(hoja['!ref'] || 'A1');

    // Encontrar última columna con datos reales
    let ultimaColConDatos = 0;
    for (let C = rango.e.c; C >= 0; C--) {
      let tieneData = false;
      for (let R = rango.s.r; R <= Math.min(rango.e.r, 30); R++) {
        const celda = hoja[XLSX.utils.encode_cell({ r: R, c: C })];
        if (celda && celda.v !== undefined && celda.v !== '') {
          tieneData = true;
          break;
        }
      }
      if (tieneData) {
        ultimaColConDatos = C;
        break;
      }
    }

    const totalColumnas = ultimaColConDatos + 1;
    this.headers = Array.from({ length: totalColumnas }, (_, i) =>
      this.indexToLetra(i)
    );

    const json: any[][] = XLSX.utils.sheet_to_json(hoja, { header: 1 });
    if (json.length > 0) {
      this.filas = json; // ← todas las filas
    }

    this.cargando = false;
    this.cdr.detectChanges();
  };
    reader.readAsArrayBuffer(archivo);
  }

  indexToLetra(i: number): string {
    let letra = '';
    while (i >= 0) {
      letra = String.fromCharCode((i % 26) + 65) + letra;
      i = Math.floor(i / 26) - 1;
    }
    return letra;
  }

  irAConfigurar() {
  this.router.navigate(['/configurar-personalizado'], {
    state: {
      headers: this.headers,
      filas: this.filas,
      archivoNombre: this.archivoNombre
    }
  });
}

}