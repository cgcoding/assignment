import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Habit, Frequency, Completion } from './habit.model';

@Injectable({
	providedIn: 'root'
})
export class HabitService {
	private apiUrl = 'http://localhost:8000/api/habit'; // Adjust to your backend's URL

	constructor(private http: HttpClient) { }

	private authHeaders(): HttpHeaders {
		const token = localStorage.getItem('token');
		return new HttpHeaders({ Authorization: `Bearer ${token}` });
	}

	getHabits(): Observable<Habit[]> {
		return this.http.get<Habit[]>(this.apiUrl, { headers: this.authHeaders() });
	}

	createHabit(habit: { name: string; frequency: Frequency }): Observable<Habit> {
		const payload = { name: habit.name.trim(), frequency: habit.frequency };
		return this.http.post<Habit>(this.apiUrl, payload, { headers: this.authHeaders() });
	}

	deleteHabit(habitId: number): Observable<void> {
		return this.http.delete<void>(`${this.apiUrl}/${habitId}`, { headers: this.authHeaders() });
	}

	completeHabit(habitId: number, isoDate: string): Observable<Completion> {
		return this.http.post<Completion>(`${this.apiUrl}/${habitId}/complete`, { date: isoDate }, { headers: this.authHeaders() });
	}

	getCompletions(habitId: number): Observable<string[]> {
		return this.http.get<string[]>(`${this.apiUrl}/${habitId}/completions`, { headers: this.authHeaders() });
	}
}
