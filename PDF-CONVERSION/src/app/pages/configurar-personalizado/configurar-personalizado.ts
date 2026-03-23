import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api';
import { ArchivoTempService } from '../../services/archivo-temp.service';

interface ColumnaItem {
  letra: string;
  nombre: string;
  indiceOriginal: number;
  seleccionada: boolean;
  
}

@Component({
  selector: 'app-configurar-personalizado',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './configurar-personalizado.html',
  styleUrl: './configurar-personalizado.css'
})
export class ConfigurarPersonalizado implements OnInit {
  columnas: ColumnaItem[] = [];
  letrasColumnas: string[] = [];
  filas: any[][] = [];
  archivoNombre = '';

  filaInicio = 23;
  orientacion: 'portrait' | 'landscape' = 'landscape';
  columnaAgrupacion = 0;
  generando = false;
  incluirComentarios = false;
  nombreEmpresa = ''; 

  // Nomenclatura
  filaNomenclaturaInicio = 7;
  filaNomenclaturaFin = 20;
  nomenclaturaDetectada: { nombre: string, abrev: string }[] = [];
  nomenclaturaSeleccionada: boolean[] = [];
  usarNomenclaturaDefault = false;
  tieneNomenclaturaEnExcel = false;
  tamanoLetra = 0; 

  readonly NOMENCLATURA_DEFAULT = [
    { nombre: 'Descanso', abrev: 'D' },
    { nombre: 'Descanso Laborado', abrev: 'DL' },
    { nombre: 'Falta por no marcar', abrev: 'F' },
    { nombre: 'Feriado Laborado', abrev: 'FL' },
    { nombre: 'Horas extras', abrev: '$' },
    { nombre: 'Incapacidad', abrev: 'I' },
    { nombre: 'Marca faltante', abrev: 'MF' },
    { nombre: 'Permiso con goce de sueldo', abrev: 'C' },
    { nombre: 'Permiso sin goce de sueldo', abrev: 'P' },
    { nombre: 'Prima Dominical', abrev: 'PD' },
    { nombre: 'Suspensión', abrev: 'S' },
    { nombre: 'Turno Laborado', abrev: 'X' },
    { nombre: 'Vacaciones', abrev: 'V' }
  ];

  constructor(
    public router: Router,
    private apiService: ApiService,
    public archivoTemp: ArchivoTempService,
    public cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    const state = history.state;
    if (state?.headers) {
      this.letrasColumnas = state.headers;
      this.filas = state.filas || [];
      this.archivoNombre = state.archivoNombre;
      this.inicializarColumnas();
      this.detectarNomenclatura();
    }
  }

    columnasSeleccionadasOrdenadas() {
    return this.columnas.filter(c => c.seleccionada);
  }

  abreviarTitulo(texto: string): string {
    const abrevs: { [key: string]: string } = {
      'nombre del colaborador': 'Nombre',
      'email del colaborador': 'Email',
      'identificador': 'Clave',
      'contrato': 'Contrato',
      'area/departamento': 'Depto',
      'posición': 'Puesto',
      'última marca (zona horaria contrato)': 'Últ. Marca',
      'zona horaria contrato': 'Zona',
    };
    const clave = texto.toLowerCase().trim();
    if (abrevs[clave]) return abrevs[clave];
    return texto.length > 10 ? texto.substring(0, 10) + '...' : texto;
  }

    fechaHoy(): string {
    const hoy = new Date();
    return hoy.toLocaleDateString('es-MX');
  }
  filasPreview(): any[][] {
    const filaIdx = this.filaInicio;
    return this.filas.slice(filaIdx, filaIdx + 5);
  }
  inicializarColumnas() {
    const filaIdx = this.filaInicio - 1;
    const fila = this.filas.length > filaIdx ? this.filas[filaIdx] : [];
    this.columnas = this.letrasColumnas.map((letra, i) => ({
      letra,
      nombre: fila[i] !== undefined && fila[i] !== null && String(fila[i]) !== ''
        ? String(fila[i]) : letra,
      indiceOriginal: i,
      seleccionada: true
    }));
  }

  onFilaInicioChange() {
    this.inicializarColumnas();
    this.cdr.detectChanges();
  }

  moverColumna(index: number, direccion: number) {
    const nuevaPos = index + direccion;
    if (nuevaPos < 0 || nuevaPos >= this.columnas.length) return;
    const temp = this.columnas[index];
    this.columnas[index] = this.columnas[nuevaPos];
    this.columnas[nuevaPos] = temp;
    this.cdr.detectChanges();
  }

  toggleColumna(i: number) {
    this.columnas[i].seleccionada = !this.columnas[i].seleccionada;
  }

  columnasElegidas(): number[] {
    return this.columnas
      .filter(c => c.seleccionada)
      .map(c => c.indiceOriginal);
  }

  columnasDisponiblesParaAgrupar() {
    return this.columnas
      .filter(c => c.seleccionada)
      .map(c => ({ index: c.indiceOriginal, letra: c.letra, nombre: c.nombre }));
  }

  detectarNomenclatura() {
  const filaInicio = this.filaNomenclaturaInicio - 1;
  const filaFin = this.filaNomenclaturaFin - 1;
  this.nomenclaturaDetectada = [];

  for (let i = filaInicio; i <= filaFin && i < this.filas.length; i++) {
    const fila = this.filas[i];
    const nombre = fila[0] !== undefined && fila[0] !== null && fila[0] !== ''
      ? String(fila[0]).trim() : null;
    const abrev = fila[1] !== undefined && fila[1] !== null && fila[1] !== ''
      ? String(fila[1]).trim() : null;

    if (!nombre || !abrev) continue;
    if (nombre === 'Nombre de política' || nombre === 'Nomenclatura') continue;

    // Validaciones estrictas para la abreviación
    const esAbreviacionValida =
      abrev.length >= 1 &&
      abrev.length <= 4 &&
      !/^\d+$/.test(abrev) &&          // no es solo números
      !/\d{4}-\d{2}-\d{2}/.test(abrev) && // no es fecha
      /^[A-Za-z$%#&*]+$/.test(abrev);  // solo letras o símbolos simples

    if (esAbreviacionValida) {
      this.nomenclaturaDetectada.push({ nombre, abrev });
    }
  }

  // Solo cuenta como nomenclatura si detectó al menos 3 entradas válidas
  this.tieneNomenclaturaEnExcel = this.nomenclaturaDetectada.length >= 3;

  if (!this.tieneNomenclaturaEnExcel) {
    this.nomenclaturaDetectada = [];
    this.usarNomenclaturaDefault = true;
    this.nomenclaturaDetectada = [...this.NOMENCLATURA_DEFAULT];
    this.nomenclaturaSeleccionada = this.nomenclaturaDetectada.map(() => true);
  } else {
    this.usarNomenclaturaDefault = false;
    this.nomenclaturaSeleccionada = this.nomenclaturaDetectada.map(() => true);
  }

  this.cdr.detectChanges();
}

  onToggleDefault() {
    if (this.usarNomenclaturaDefault) {
      this.nomenclaturaDetectada = [...this.NOMENCLATURA_DEFAULT];
      this.nomenclaturaSeleccionada = this.nomenclaturaDetectada.map(() => true);
    } else {
      this.nomenclaturaDetectada = [];
      this.nomenclaturaSeleccionada = [];
    }
    this.cdr.detectChanges();
  }
  toggleNomenclatura(i: number) {
    this.nomenclaturaSeleccionada[i] = !this.nomenclaturaSeleccionada[i];
  }

  estaSeleccionadaNomenclatura(i: number): boolean {
    return this.nomenclaturaSeleccionada[i];
  }

  nomenclaturaElegida() {
    return this.nomenclaturaDetectada.filter((_, i) => this.nomenclaturaSeleccionada[i]);
  }

  camposValidos(): boolean {
    return this.filaInicio > 0 &&
           this.columnasElegidas().length > 0 &&
           !!this.archivoTemp.archivo;
  }

  generarPdf() {
    if (!this.camposValidos()) return;
    this.generando = true;
    this.cdr.detectChanges();

    const formData = new FormData();
    formData.append('archivo', this.archivoTemp.archivo!);
    formData.append('formato', 'personalizado');
    formData.append('fila_inicio', String(this.filaInicio));
    formData.append('orientacion', this.orientacion);
    formData.append('columnas', JSON.stringify(this.columnasElegidas()));
    formData.append('columna_agrupacion', String(this.columnaAgrupacion));
    formData.append('nomenclatura', JSON.stringify(this.nomenclaturaElegida()));
    formData.append('incluir_comentarios', String(this.incluirComentarios));
    formData.append('nombre_empresa', this.nombreEmpresa);
    formData.append('tamano_letra', String(this.tamanoLetra));

    this.apiService.generarPdfPersonalizado(formData).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${this.archivoNombre}_reporte.pdf`;
        link.click();
        window.URL.revokeObjectURL(url);
        this.generando = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error:', err);
        this.generando = false;
        this.cdr.detectChanges();
      }
    });
  }
}