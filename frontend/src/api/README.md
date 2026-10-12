# `src/api`: backend API calls

Every call to the FastAPI backend goes through this folder. Pages import functions from here; they never call `fetch` themselves.

```
src/api/
├── config.ts          # reads VITE_API_* from frontend/.env
├── endpoints.ts       # every backend route path, grouped by module
├── client.ts          # apiRequest / apiGet / apiPost + ApiError (the only fetch() in the app)
├── authToken.ts       # stores the access token, signals 401s to AuthProvider
├── userMapper.ts      # UserDto + toUser(), shared by the user-related api files
└── api.<module>[.<page>].ts   # one file per backend module or page
    api.auth.ts                # login, logout, getCurrentUser
    api.users.ts               # getMyProfile, updateMyProfile (ProfilePage)
    api.admin.users.ts         # listUsers, createUser, updateUser, resetPassword (AdminUsersPage)
    api.admin.dashboard.ts     # getDashboard (AdminDashboardPage)
    api.topics.ts              # suggestTopic, getDailyTopic, createCustomTopic, getReadingMaterial (Topic, Prepare, Home)
```

## Naming

One file per backend module, or per page when a module's pages use different endpoints:

| File                     | For                                                     |
| ------------------------ | ------------------------------------------------------- |
| `api.auth.ts`            | Login, logout, current user                             |
| `api.admin.dashboard.ts` | Admin dashboard KPIs/charts (when the backend has them) |
| `api.admin.users.ts`     | Admin user management                                   |
| `api.session.ts`         | Talk session create/upload/status                       |
| `api.feedback.ts`        | Feedback for a session                                  |

Import a module as a namespace so call sites read clearly:

```ts
import * as authApi from '@/api/api.auth'

const user = await authApi.login(email, password)
```

## Writing a new API file

1. Add the route paths to `endpoints.ts`:

   ```ts
   adminDashboard: { summary: '/admin/dashboard/summary' },
   ```

2. Create `api.admin.dashboard.ts`:

   ```ts
   import { apiGet } from './client'
   import { ENDPOINTS } from './endpoints'

   // Backend shape (snake_case, exactly as the API returns it)
   interface DashboardSummaryDto {
     total_users: number
     active_users: number
   }

   // App shape (camelCase, what pages use)
   export interface DashboardSummary {
     totalUsers: number
     activeUsers: number
   }

   export async function getDashboardSummary(): Promise<DashboardSummary> {
     const dto = await apiGet<DashboardSummaryDto>(ENDPOINTS.adminDashboard.summary)
     return { totalUsers: dto.total_users, activeUsers: dto.active_users }
   }
   ```

3. Call it from the page (or a hook used by the page):

   ```ts
   import * as dashboardApi from '@/api/api.admin.dashboard'
   const summary = await dashboardApi.getDashboardSummary()
   ```

## Rules

- **DTOs stay in the api file.** Define the backend's snake_case response as `...Dto` and map it to the app's types (`@/core/types`) before returning. Pages never see snake_case.
- **The token is automatic.** `client.ts` adds `Authorization: Bearer <token>` to every request. Pass `{ auth: false }` only for public routes (login).
- **Errors are `ApiError`.** It has `status` (0 = network error or timeout) and a user-readable `message`. Map status codes to page copy in the page, as `LoginPage` does.
- **401 signs the user out.** If a protected request returns 401, `client.ts` clears the token and `AuthProvider` signs the user out. Pages don't need to handle it.
- **No base URLs in code.** They come from `.env` via `config.ts`. Route paths live only in `endpoints.ts`.
