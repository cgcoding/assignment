import { isPlatformBrowser } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Inject, Injectable, PLATFORM_ID } from '@angular/core';
import { Observable } from 'rxjs';

export interface Habit {
  id: number;
  name: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  user_id: number;
}

export interface HabitCompletionIn {
  completed_on: string;
}

export interface HabitCompletionOut {
  id: number;
  habit_id: number;
  user_id: number;
  completed_on: string;
  period_start: string;
}

@Injectable({
  providedIn: 'root'
})
export class HabitService {
  private apiUrl = 'http://localhost:8000/api/habit';

  constructor(
    private http: HttpClient,
    @Inject(PLATFORM_ID) private platformId: object
  ) {}

  private getAuthHeaders(): HttpHeaders {
    let token = '';
    if (isPlatformBrowser(this.platformId)) {
      token = localStorage.getItem('token') || '';
    }

    return new HttpHeaders({
      Authorization: `Bearer ${token}`
    });
  }

  addHabit(habitData: Partial<Habit>): Observable<Habit> {
    return this.http.post<Habit>(`${this.apiUrl}/`, habitData, {
      headers: this.getAuthHeaders()
    });
  }

  getHabits(): Observable<Habit[]> {
    return this.http.get<Habit[]>(`${this.apiUrl}/`, {
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

  getCompletions(habitId: number): Observable<HabitCompletionOut[]> {
    return this.http.get<HabitCompletionOut[]>(`${this.apiUrl}/${habitId}/completions`, {
      headers: this.getAuthHeaders()
    });
  }
}
