import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import ScheduleList from './ScheduleList';
import * as generated from '../api/generated';
import type { ScheduleResponse } from '../api/generated';

const mockSchedules: ScheduleResponse[] = [
  { schedule_id: 1, name: 'Fall 2025', semester_id: 1, draft: false, campus: 1, active: true },
  { schedule_id: 2, name: 'Spring 2026', semester_id: 2, draft: true, campus: 1, active: false },
];

function renderList() {
  return render(
    <MemoryRouter initialEntries={['/schedules']}>
      <Routes>
        <Route path="/schedules" element={<ScheduleList />} />
        <Route path="/schedules/:id" element={<div data-testid="schedule-view" />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ScheduleList page', () => {
  let mockGetSchedules: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockGetSchedules = vi.fn();
    vi.spyOn(generated, 'getAutomatedCourseSchedulerAPI').mockReturnValue({
      getSchedulesSchedulesGet: mockGetSchedules,
    } as unknown as ReturnType<typeof generated.getAutomatedCourseSchedulerAPI>);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows loading spinner while fetching', () => {
    mockGetSchedules.mockReturnValue(new Promise(() => {}));
    renderList();
    expect(screen.getByText('Loading schedules…')).toBeInTheDocument();
  });

  it('renders a card for each schedule', async () => {
    mockGetSchedules.mockResolvedValue(mockSchedules);
    renderList();
    await waitFor(() => expect(screen.getByText('Fall 2025')).toBeInTheDocument());
    expect(screen.getByText('Spring 2026')).toBeInTheDocument();
  });

  it('shows "Published" badge for non-draft schedules', async () => {
    mockGetSchedules.mockResolvedValue(mockSchedules);
    renderList();
    await waitFor(() => expect(screen.getByText('Published')).toBeInTheDocument());
  });

  it('shows "Draft" badge for draft schedules', async () => {
    mockGetSchedules.mockResolvedValue(mockSchedules);
    renderList();
    await waitFor(() => expect(screen.getByText('Draft')).toBeInTheDocument());
  });

  it('shows "Active" badge for active schedules', async () => {
    mockGetSchedules.mockResolvedValue(mockSchedules);
    renderList();
    await waitFor(() => expect(screen.getByText('Active')).toBeInTheDocument());
  });

  it('navigates to schedule view on card click', async () => {
    const user = userEvent.setup();
    mockGetSchedules.mockResolvedValue(mockSchedules);
    renderList();

    await waitFor(() => expect(screen.getByText('Fall 2025')).toBeInTheDocument());
    await user.click(screen.getByText('Fall 2025'));

    expect(screen.getByTestId('schedule-view')).toBeInTheDocument();
  });

  it('shows empty state when no schedules exist', async () => {
    mockGetSchedules.mockResolvedValue([]);
    renderList();
    await waitFor(() => expect(screen.getByText('No schedules found.')).toBeInTheDocument());
  });

  it('shows error message when fetch fails', async () => {
    mockGetSchedules.mockRejectedValue(new Error('Network error'));
    renderList();
    await waitFor(() =>
      expect(screen.getByText('Failed to load schedules.')).toBeInTheDocument(),
    );
  });

  it('renders the page heading', async () => {
    mockGetSchedules.mockResolvedValue([]);
    renderList();
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Schedules' })).toBeInTheDocument(),
    );
  });
});
