import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-formato-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './formato-modal.html',
  styleUrl: './formato-modal.css'
})
export class FormatoModal {
  @Output() formatoSeleccionado = new EventEmitter<string>();
  @Output() cerrar = new EventEmitter<void>();

  elegir(formato: string) {
    this.formatoSeleccionado.emit(formato);
  }
}