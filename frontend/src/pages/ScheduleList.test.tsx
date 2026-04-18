import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import ScheduleList from './ScheduleList';
import * as generated from '../api/generated';
import type { ScheduleResponse, UserResponse } from '../api/generated';

const mockSchedules: ScheduleResponse[] = [
  { schedule_id: 1, name: 'Fall 2025', semester_id: 1, draft: false, campus: 1, active: true },
  { schedule_id: 2, name: 'Spring 2026', semester_id: 2, draft: true, campus: 1, active: false },
];

const adminUser: UserResponse = {
  user_id: 1,
  nuid: 100001,
  first_name: 'Ada',
  last_name: 'Admin',
  email: 'ada@northeastern.edu',
  role: 'ADMIN',
  active: true,
};

const viewerUser: UserResponse = {
  ...adminUser,
  user_id: 2,
  first_name: 'Vic',
  last_name: 'Viewer',
  email: 'vic@northeastern.edu',
  role: 'VIEWER',
};

type ApiMocks = {
  getSchedulesSchedulesGet: ReturnType<typeof vi.fn>;
  getMeApiUsersMeGet: ReturnType<typeof vi.fn>;
  updateScheduleSchedulesScheduleIdPut: ReturnType<typeof vi.fn>;
  deleteScheduleSchedulesScheduleIdDelete: ReturnType<typeof vi.fn>;
  getAllSemestersSemestersGet: ReturnType<typeof vi.fn>;
  getAllCampusesCampusesGet: ReturnType<typeof vi.fn>;
  createScheduleSchedulesPost: ReturnType<typeof vi.fn>;
};

let api: ApiMocks;

function mockApi(overrides: Partial<ApiMocks> = {}) {
  api = {
    getSchedulesSchedulesGet: vi.fn().mockResolvedValue(mockSchedules),
    getMeApiUsersMeGet: vi.fn().mockResolvedValue(viewerUser),
    updateScheduleSchedulesScheduleIdPut: vi.fn(),
    deleteScheduleSchedulesScheduleIdDelete: vi.fn().mockResolvedValue(undefined),
    getAllSemestersSemestersGet: vi.fn().mockResolvedValue([]),
    getAllCampusesCampusesGet: vi.fn().mockResolvedValue([]),
    createScheduleSchedulesPost: vi.fn(),
    ...overrides,
  };
  vi.spyOn(generated, 'getAutomatedCourseSchedulerAPI').mockReturnValue(
    api as unknown as ReturnType<typeof generated.getAutomatedCourseSchedulerAPI>,
  );
}

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
  beforeEach(() => {
    mockApi();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows loading spinner while fetching', () => {
    mockApi({ getSchedulesSchedulesGet: vi.fn().mockReturnValue(new Promise(() => {})) });
    renderList();
    expect(screen.getByText('Loading schedules...')).toBeInTheDocument();
  });

  it('renders a card for each schedule', async () => {
    renderList();
    expect(await screen.findByText('Fall 2025')).toBeInTheDocument();
    expect(screen.getByText('Spring 2026')).toBeInTheDocument();
  });

  it('shows "Published" badge for non-draft schedules', async () => {
    renderList();
    expect(await screen.findByText('Published')).toBeInTheDocument();
  });

  it('shows "Draft" badge for draft schedules', async () => {
    renderList();
    expect(await screen.findByText('Draft')).toBeInTheDocument();
  });

  it('navigates to schedule view on card click', async () => {
    const user = userEvent.setup();
    renderList();

    const card = await screen.findByRole('button', { name: /Fall 2025/ });
    await user.click(card);

    expect(screen.getByTestId('schedule-view')).toBeInTheDocument();
  });

  it('shows empty state when no schedules exist', async () => {
    mockApi({ getSchedulesSchedulesGet: vi.fn().mockResolvedValue([]) });
    renderList();
    expect(await screen.findByText('No schedules found.')).toBeInTheDocument();
  });

  it('shows error message when fetch fails', async () => {
    mockApi({ getSchedulesSchedulesGet: vi.fn().mockRejectedValue(new Error('Network error')) });
    renderList();
    expect(await screen.findByText('Failed to load schedules.')).toBeInTheDocument();
  });

  it('renders the page heading', async () => {
    renderList();
    expect(
      await screen.findByRole('heading', { name: 'Schedules' }),
    ).toBeInTheDocument();
  });

  it('hides "New Schedule" button for non-admin users', async () => {
    renderList();
    await screen.findByText('Fall 2025');
    expect(screen.queryByRole('button', { name: /New Schedule/ })).not.toBeInTheDocument();
  });

  it('shows "New Schedule" button for admin users', async () => {
    mockApi({ getMeApiUsersMeGet: vi.fn().mockResolvedValue(adminUser) });
    renderList();
    expect(
      await screen.findByRole('button', { name: /New Schedule/ }),
    ).toBeInTheDocument();
  });

  it('hides edit controls on schedule cards for non-admin users', async () => {
    renderList();
    await screen.findByText('Fall 2025');
    expect(screen.queryByRole('button', { name: 'Edit schedule' })).not.toBeInTheDocument();
  });

  it('lets admins save a renamed schedule', async () => {
    const user = userEvent.setup();
    const updated: ScheduleResponse = { ...mockSchedules[0], name: 'Fall 2025 (renamed)' };
    mockApi({
      getMeApiUsersMeGet: vi.fn().mockResolvedValue(adminUser),
      updateScheduleSchedulesScheduleIdPut: vi.fn().mockResolvedValue(updated),
    });
    renderList();

    await screen.findByText('Fall 2025');
    const editButtons = await screen.findAllByRole('button', { name: 'Edit schedule' });
    await user.click(editButtons[0]);

    const nameInput = screen.getByDisplayValue('Fall 2025');
    await user.clear(nameInput);
    await user.type(nameInput, 'Fall 2025 (renamed)');
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() =>
      expect(api.updateScheduleSchedulesScheduleIdPut).toHaveBeenCalledWith(1, {
        name: 'Fall 2025 (renamed)',
      }),
    );
    expect(await screen.findByText('Fall 2025 (renamed)')).toBeInTheDocument();
  });

  it('deletes a schedule after confirming', async () => {
    const user = userEvent.setup();
    mockApi({ getMeApiUsersMeGet: vi.fn().mockResolvedValue(adminUser) });
    renderList();

    await screen.findByText('Fall 2025');
    const editButtons = await screen.findAllByRole('button', { name: 'Edit schedule' });
    await user.click(editButtons[0]);

    await user.click(screen.getByRole('button', { name: /Delete schedule/ }));
    await user.click(screen.getByRole('button', { name: 'Yes' }));

    await waitFor(() =>
      expect(api.deleteScheduleSchedulesScheduleIdDelete).toHaveBeenCalledWith(1),
    );
    await waitFor(() => expect(screen.queryByText('Fall 2025')).not.toBeInTheDocument());
    expect(screen.getByText('Spring 2026')).toBeInTheDocument();
  });

  it('cancels delete when "No" is clicked', async () => {
    const user = userEvent.setup();
    mockApi({ getMeApiUsersMeGet: vi.fn().mockResolvedValue(adminUser) });
    renderList();

    await screen.findByText('Fall 2025');
    const editButtons = await screen.findAllByRole('button', { name: 'Edit schedule' });
    await user.click(editButtons[0]);

    await user.click(screen.getByRole('button', { name: /Delete schedule/ }));
    await user.click(screen.getByRole('button', { name: 'No' }));

    expect(screen.getByRole('button', { name: /Delete schedule/ })).toBeInTheDocument();
    expect(api.deleteScheduleSchedulesScheduleIdDelete).not.toHaveBeenCalled();
  });

  it('opens the create-schedule modal when admin clicks "New Schedule"', async () => {
    const user = userEvent.setup();
    mockApi({ getMeApiUsersMeGet: vi.fn().mockResolvedValue(adminUser) });
    renderList();

    await user.click(await screen.findByRole('button', { name: /New Schedule/ }));

    const dialogHeading = await screen.findByRole('heading', { name: 'New Schedule' });
    const modal = dialogHeading.closest('div')?.parentElement as HTMLElement;
    expect(within(modal).getByText('Upload CSV Files')).toBeInTheDocument();
    expect(within(modal).getByRole('button', { name: 'Next' })).toBeDisabled();
  });
});
