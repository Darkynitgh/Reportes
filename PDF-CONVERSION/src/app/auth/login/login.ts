import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';
import { ChangeDetectorRef } from '@angular/core';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent {
  usuario = '';
  password = '';
  error = '';

  constructor(private router: Router, private auth: AuthService, private cd: ChangeDetectorRef) {}

  ingresar() {
    this.auth.login(this.usuario, this.password).subscribe({
      next: (res) => {
        this.auth.guardarToken(res.access_token);
        this.router.navigate(['/dashboard']);
      },
      error: () => {
        this.error = 'Usuario o contraseña incorrectos';
        this.cd.detectChanges();
      }
    });
  }
}