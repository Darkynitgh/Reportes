import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

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

  constructor(private router: Router) {}

  ingresar() {
    // Por ahora pasa directo, aquí conectarás AuthService después
    this.router.navigate(['/dashboard']);
  }
}