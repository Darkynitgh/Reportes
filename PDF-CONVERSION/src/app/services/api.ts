import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  generarPdf(archivo: File, formato: string): Observable<Blob> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    formData.append('formato', formato);

    return this.http.post(`${this.apiUrl}/generar-pdf`, formData, {
      responseType: 'blob'
    });
  }

  generarPdfPersonalizado(formData: FormData): Observable<Blob> {
  return this.http.post(`${this.apiUrl}/generar-pdf`, formData, {
    responseType: 'blob'
  });
}
}