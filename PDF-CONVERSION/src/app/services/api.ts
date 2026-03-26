import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://192.168.2.178:8000';

  constructor(private http: HttpClient) {}

  generarPdf(archivo: File, formato: string): Observable<Blob> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    formData.append('formato', formato);

    return this.http.post(`${this.apiUrl}/generar-pdf`, formData, {
      responseType: 'blob'
    });
  }
  
  combinarPdfs(blobs: Blob[]): Observable<Blob> {
    const formData = new FormData();
    blobs.forEach((blob, i) => {
      formData.append('archivos', blob, `reporte_${i + 1}.pdf`);
    });
    return this.http.post(`${this.apiUrl}/combinar-pdfs`, formData, {
      responseType: 'blob'
    });
  }

  generarPdfPersonalizado(formData: FormData): Observable<Blob> {
  return this.http.post(`${this.apiUrl}/generar-pdf`, formData, {
    responseType: 'blob'
  });
}
}