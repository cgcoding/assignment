export type HabitFrequency = 'daily' | 'weekly';

export interface Habit {
	id: number;
	userId: number;
	name: string;
	frequency: HabitFrequency;
}

export interface HabitCompletionIn {
	completion_date: string;
}

export interface HabitStreak {
	habitId: number;
	name: string;
	frequency: HabitFrequency;
	current_streak: number;
	longest_streak: number;
	last_completed_date: string | null;
}
