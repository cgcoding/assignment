import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Habit, HabitService } from './habit.service';

@Component({
  selector: 'app-habit',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './habit.html'
})
export class HabitComponent implements OnInit {
  habits: Habit[] = [];
  errorMessage: string | null = null;

  newHabit: { name: string; frequency: 'daily' | 'weekly' | 'monthly' } = {
    name: '',
    frequency: 'daily'
  };

  completionDateByHabitId: Record<number, string> = {};

  constructor(private habitService: HabitService) {}

  ngOnInit(): void {
    this.getHabits();
  }

  getHabits(): void {
    this.habitService.getHabits().subscribe({
      next: (data) => {
        this.habits = data;
      },
      error: (err) => {
        this.errorMessage = err?.error?.detail || 'Could not fetch habits';
      }
    });
  }

  addHabit(): void {
    this.errorMessage = null;
    if (!this.newHabit.name.trim()) {
      this.errorMessage = 'Habit name is required';
      return;
    }

    this.habitService.addHabit(this.newHabit).subscribe({
      next: () => {
        this.newHabit = { name: '', frequency: 'daily' };
        this.getHabits();
      },
      error: (err) => {
        this.errorMessage = err?.error?.detail || 'Could not create habit';
      }
    });
  }

  deleteHabit(habitId: number): void {
    this.habitService.deleteHabit(habitId).subscribe({
      next: () => {
        this.habits = this.habits.filter((h) => h.id !== habitId);
      },
      error: (err) => {
        this.errorMessage = err?.error?.detail || 'Could not delete habit';
      }
    });
  }

  markComplete(habitId: number): void {
    this.errorMessage = null;
    const completed_on = this.completionDateByHabitId[habitId] || this.today();

    this.habitService.markComplete(habitId, { completed_on }).subscribe({
      next: () => {
        this.completionDateByHabitId[habitId] = completed_on;
      },
      error: (err) => {
        this.errorMessage = err?.error?.detail || 'Could not mark complete';
      }
    });
  }

  today(): string {
    return new Date().toISOString().slice(0, 10);
  }
}
