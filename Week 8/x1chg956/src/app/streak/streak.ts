import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HabitService } from '../habit/habit.service';
import { Habit } from '../habit/habit.model';

@Component({
	selector: 'app-streak',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterLink],
	templateUrl: './streak.html'
})
export class StreakComponent implements OnInit {
	habits: Habit[] = [];
	selectedHabitId: number | null = null;
	streakCount: number | null = null;
	errorMessage: string | null = null;

	constructor(private habitService: HabitService, private router: Router, private cdr: ChangeDetectorRef) { }

	ngOnInit(): void {
		this.habitService.getHabits().subscribe({
			next: (habits) => {
				this.habits = habits;
				this.cdr.markForCheck();
			},
			error: (err) => {
				this.errorMessage = 'Failed to load habits.';
				console.error(err);
				this.cdr.markForCheck();
			}
		});
	}

	get selectedHabit(): Habit | undefined {
		return this.habits.find(h => h.habitId === this.selectedHabitId) ?? undefined;
	}

	calculateStreak(): void {
		const habit = this.selectedHabit;
		if (!habit) return;
		this.errorMessage = null;
		this.streakCount = null;
		this.habitService.getCompletions(habit.habitId).subscribe({
			next: (dates) => {
				this.streakCount = habit.frequency === 'Daily'
					? this.computeDailyStreak(dates)
					: this.computeWeeklyStreak(dates);
				this.cdr.markForCheck();
			},
			error: (err) => {
				this.errorMessage = 'Failed to load completions.';
				console.error(err);
				this.cdr.markForCheck();
			}
		});
	}

	logout(): void {
		localStorage.removeItem('token');
		this.router.navigate(['/auth']);
	}

	private computeDailyStreak(dates: string[]): number {
		const completed = new Set(dates);
		let cursor = this.startOfToday();
		if (!completed.has(this.toIso(cursor))) {
			cursor = this.addDays(cursor, -1);
		}
		let streak = 0;
		while (completed.has(this.toIso(cursor))) {
			streak++;
			cursor = this.addDays(cursor, -1);
		}
		return streak;
	}

	private computeWeeklyStreak(dates: string[]): number {
		const completed = new Set(dates);
		let cursor = this.mondayOf(this.startOfToday());
		if (!completed.has(this.toIso(cursor))) {
			cursor = this.addDays(cursor, -7);
		}
		let streak = 0;
		while (completed.has(this.toIso(cursor))) {
			streak++;
			cursor = this.addDays(cursor, -7);
		}
		return streak;
	}

	private startOfToday(): Date {
		const d = new Date();
		d.setHours(0, 0, 0, 0);
		return d;
	}

	private mondayOf(d: Date): Date {
		const day = d.getDay(); // Sun=0 .. Sat=6
		const diffToMonday = day === 0 ? -6 : 1 - day;
		return this.addDays(d, diffToMonday);
	}

	private addDays(d: Date, n: number): Date {
		const copy = new Date(d);
		copy.setDate(copy.getDate() + n);
		return copy;
	}

	private toIso(d: Date): string {
		const yyyy = d.getFullYear();
		const mm = String(d.getMonth() + 1).padStart(2, '0');
		const dd = String(d.getDate()).padStart(2, '0');
		return `${yyyy}-${mm}-${dd}`;
	}
}
