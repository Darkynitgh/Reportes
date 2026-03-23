import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ArchivoTempService {
  archivo: File | null = null;
}