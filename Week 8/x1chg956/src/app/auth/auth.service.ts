// src/app/auth/auth.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AuthResponse {
	token: string;
	user?: {
		id: number;
		email: string;
	};
}

@Injectable({
	providedIn: 'root'
})
export class AuthService {
	private apiUrl = 'http://localhost:8000/api/auth'; // Adjust to your backend's URL

	constructor(private http: HttpClient) { }

	// login takes a credentials object with email and password properties and returns an 
	// Observable of type AuthResponse. To do this it sends a POST request to the 
	// /login  endpoint of the backend API.
	login(credentials: { email: string; password: string })
		: Observable<AuthResponse> {
		return this.http.post<AuthResponse>(`${this.apiUrl}/login`, credentials);
	}

	signup(details: { email: string; password: string; confirmPassword: string })
		: Observable<AuthResponse> {
		return this.http.post<AuthResponse>(`${this.apiUrl}/signup`, details);
	}
}
