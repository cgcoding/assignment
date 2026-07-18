import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms'; // 
import { AuthService, AuthResponse } from './auth.service';

@Component({
	selector: 'app-auth',
	standalone: true,
	imports: [CommonModule, FormsModule],
	templateUrl: './auth.html',
	styleUrl: './auth.css'
})
export class AuthComponent {
	mode: 'login' | 'signup' = 'login';

	loginData = {
		email: '',
		password: '',
	};
	signupData = {
		email: '',
		password: '',
		confirmPassword: '',
	};
	authResponse: AuthResponse | null = null;
	errorMessage: string | null = null;

	constructor(private authService: AuthService, 
		        private router: Router) { }

	toggleMode(): void {
		this.mode = this.mode === 'login' ? 'signup' : 'login';
		this.errorMessage = null;
		this.authResponse = null;
	}
	onSubmit(): void { 
		this.errorMessage = null;
		if (this.mode === 'login') {
			this.authService.login(this.loginData).subscribe({
				next: (response) => {
					this.authResponse = response;
					localStorage.setItem('token', response.token);  // Store token
					console.log('Login successful:', response);
					this.router.navigate(['/habit']);
				},
				error: (err) => {
					this.errorMessage = 'Login failed. Please try again.';
					console.error(err);
				},
			});
		} else {
			// Basic check: ensure password and confirmPassword match
			if (this.signupData.password !== this.signupData.confirmPassword) {
				this.errorMessage = "Passwords don't match.";
				return;
			}
			this.authService.signup(this.signupData).subscribe({
				next: (response) => {
					this.authResponse = response;
					localStorage.setItem('token', response.token);  // the backend recognizes the user on future API calls thru tokens
					console.log('Signup successful:', response);
					this.router.navigate(['/habit']);
				},
				error: (err) => {
					this.errorMessage = 'Signup failed. Please try again.';
					console.error(err);
				},
			});
		}
	}
}



