
import { Routes } from '@angular/router';
import { AuthComponent } from './auth/auth';
// import { HabitComponent } from './habit/habit';
// import { StreakComponent } from './streak/streak';
export const routes: Routes = [
	{ path: 'auth', component: AuthComponent },
	// { path: 'habit', component: HabitComponent },
	// { path: 'streak', component: StreakComponent },
	{ path: '', redirectTo: 'auth', pathMatch: 'full' },
	{ path: '**', redirectTo: 'auth' }
];
