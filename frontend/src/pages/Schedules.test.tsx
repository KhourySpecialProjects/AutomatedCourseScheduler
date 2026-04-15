import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import Schedules from './Schedules';
import * as wsModule from '../hooks/useScheduleWebSocket';
import * as generated from '../api/generated';
import type { SectionRichResponse } from '../api/generated';

// ── Auth0 mock ────────────────────────────────────────────────────────────────
vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    getAccessTokenSilently: vi.fn().mockResolvedValue('mock-token'),
    user: { name: 'Test User', email: 'test@test.com' },
  }),
}));

// ── Child component mock ──────────────────────────────────────────────────────
vi.mock('../components/ScheduleSectionRowView', () => ({
  default: ({ sections, scheduleId }: { sections: SectionRichResponse[]; scheduleId: number }) => (
    <div data-testid="section-row-view" data-schedule-id={scheduleId}>
      {sections.map((s) => (
        <div key={s.section_id} data-testid="section-item">{s.course.name}</div>
      ))}
    </div>
  ),
}));

// ── Fixtures ──────────────────────────────────────────────────────────────────
const mockSection: SectionRichResponse = {
  section_id: 1,
  section_number: 1,
  capacity: 30,
  schedule_id: 42,
  course: { course_id: 10, name: 'Algorithms', description: 'Algo course', credits: 4 },
  time_block: { time_block_id: 5, days: 'MWR', start_time: '09:00', end_time: '10:30' },
  instructors: [],
};

const defaultWsReturn: wsModule.UseScheduleWebSocketResult = {
  sections: [],
  locks: new Map(),
  loading: false,
  status: 'connected',
  warnings: new Map(),
  dismissWarning: vi.fn(),
};

function renderAtRoute(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/schedules/:scheduleId" element={<Schedules />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('Schedules page', () => {
  beforeEach(() => {
    vi.spyOn(generated, 'getAutomatedCourseSchedulerAPI').mockReturnValue({
      getScheduleSchedulesScheduleIdGet: vi.fn().mockResolvedValue({
        schedule_id: 42, name: 'Fall 2025', semester_id: 1, draft: false, campus: 1, active: true,
      }),
      getAllCampusesCampusesGet: vi.fn().mockResolvedValue([
        { campus_id: 1, name: 'Boston', active: true },
      ]),
      getFacultyFacultyGet: vi.fn().mockResolvedValue([
        { NUID: 100005 },
      ]),
      getMeApiUsersMeGet: vi.fn().mockResolvedValue([
        {user_id: 1, nuid: 100005, first_name: "John", last_name: "Doe", email: "j.doe@northeastern.edu",role: "VIEWER", active: true}
      ])
    } as unknown as ReturnType<typeof generated.getAutomatedCourseSchedulerAPI>);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows spinner while WebSocket is loading', () => {
    vi.spyOn(wsModule, 'useScheduleWebSocket').mockReturnValue({
      ...defaultWsReturn, loading: true, status: 'connecting',
    });
    renderAtRoute('/schedules/42');
    expect(screen.getAllByText('Connecting…').length).toBeGreaterThan(0);
    expect(screen.queryByTestId('section-row-view')).not.toBeInTheDocument();
  });

  it('renders ScheduleSectionRowView with sections once loaded', () => {
    vi.spyOn(wsModule, 'useScheduleWebSocket').mockReturnValue({
      ...defaultWsReturn, sections: [mockSection],
    });
    renderAtRoute('/schedules/42');

    const view = screen.getByTestId('section-row-view');
    expect(view).toHaveAttribute('data-schedule-id', '42');
    expect(screen.getByText('Algorithms')).toBeInTheDocument();
  });

  it('passes parsed scheduleId from URL to the WebSocket hook', () => {
    const hookSpy = vi.spyOn(wsModule, 'useScheduleWebSocket').mockReturnValue(defaultWsReturn);
    renderAtRoute('/schedules/7');
    expect(hookSpy).toHaveBeenCalledWith(7);
  });

  it('shows "Invalid schedule ID" for a non-numeric route param', () => {
    render(
      <MemoryRouter initialEntries={['/schedules/abc']}>
        <Routes>
          <Route path="/schedules/:scheduleId" element={<Schedules />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText('Invalid schedule ID.')).toBeInTheDocument();
  });

  it('shows Live indicator when connected', () => {
    vi.spyOn(wsModule, 'useScheduleWebSocket').mockReturnValue({
      ...defaultWsReturn, status: 'connected',
    });
    renderAtRoute('/schedules/42');
    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  it('shows Disconnected indicator when socket drops', () => {
    vi.spyOn(wsModule, 'useScheduleWebSocket').mockReturnValue({
      ...defaultWsReturn, status: 'disconnected',
    });
    renderAtRoute('/schedules/42');
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });

  it('renders breadcrumb link back to /schedules', () => {
    vi.spyOn(wsModule, 'useScheduleWebSocket').mockReturnValue(defaultWsReturn);
    renderAtRoute('/schedules/42');
    expect(screen.getByRole('link', { name: 'Schedules' })).toHaveAttribute('href', '/schedules');
  });

  it('displays schedule name fetched from API', async () => {
    vi.spyOn(wsModule, 'useScheduleWebSocket').mockReturnValue(defaultWsReturn);
    renderAtRoute('/schedules/42');
    expect(await screen.findByRole('heading', { name: 'Fall 2025' })).toBeInTheDocument();
  });
});
