import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

import { Habit, HabitCompletionIn, HabitStreak } from './habit.model';

@Injectable({
	providedIn: 'root'
})
export class HabitService {
	private apiUrl = 'http://localhost:8000/api/habit';

	constructor(private http: HttpClient) { }

	private getAuthHeaders(): HttpHeaders {
		let headers = new HttpHeaders({
			'Content-Type': 'application/json'
		});

		if (typeof window === 'undefined') {
			return headers;
		}

		const token = localStorage.getItem('token');
		if (token) {
			headers = headers.set('Authorization', `Bearer ${token}`);
		}

		return headers;
	}

	getHabits(): Observable<Habit[]> {
		return this.http.get<Habit[]>(`${this.apiUrl}/`, {
			headers: this.getAuthHeaders()
		});
	}

	addHabit(habitData: Partial<Habit>): Observable<Habit> {
		return this.http.post<Habit>(`${this.apiUrl}/`, habitData, {
			headers: this.getAuthHeaders()
		});
	}

	deleteHabit(habitId: number): Observable<unknown> {
		return this.http.delete(`${this.apiUrl}/${habitId}`, {
			headers: this.getAuthHeaders()
		});
	}

	markComplete(habitId: number, completionData: HabitCompletionIn): Observable<unknown> {
		return this.http.post(`${this.apiUrl}/${habitId}/complete`, completionData, {
			headers: this.getAuthHeaders()
		});
	}

	getStreaks(): Observable<HabitStreak[]> {
		return this.http.get<HabitStreak[]>(`${this.apiUrl}/streaks`, {
			headers: this.getAuthHeaders()
		});
	}
}
