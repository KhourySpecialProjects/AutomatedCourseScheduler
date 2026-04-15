import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import Faculty from './Faculty';
import * as generated from '../api/generated';
import type { InviteLinkResponse, UserResponse } from '../api/generated';

// jsdom doesn't implement URL.createObjectURL / revokeObjectURL — define stubs
// so vi.spyOn can wrap them in beforeEach.
if (!URL.createObjectURL) {
  URL.createObjectURL = () => '';
}
if (!URL.revokeObjectURL) {
  URL.revokeObjectURL = () => {};
}

const mockAdmin: UserResponse = {
  user_id: 1,
  nuid: 9999,
  first_name: 'Admin',
  last_name: 'User',
  email: 'admin@example.com',
  role: 'ADMIN',
  active: true,
};

const mockInviteRows: InviteLinkResponse[] = [
  {
    first_name: 'Jane',
    last_name: 'Doe',
    email: 'jane@example.com',
    invite_link: 'https://auth0.example.com/authorize?login_hint=jane%40example.com',
  },
  {
    first_name: 'Bob',
    last_name: 'Smith',
    email: 'bob@example.com',
    invite_link: 'https://auth0.example.com/authorize?login_hint=bob%40example.com',
  },
];

describe('Faculty page — Export Invite CSV', () => {
  let mockApi: Record<string, ReturnType<typeof vi.fn>>;
  let createObjectURLSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    // @ts-expect-error — vi.spyOn doesn't resolve static methods on URL
    createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url');
    vi.spyOn(URL, 'revokeObjectURL').mockReturnValue(undefined);

    mockApi = {
      getMeApiUsersMeGet: vi.fn().mockResolvedValue(mockAdmin),
      getAllCampusesCampusesGet: vi.fn().mockResolvedValue([]),
      getSchedulesSchedulesGet: vi.fn().mockResolvedValue([]),
      listUsersApiUsersGet: vi.fn().mockResolvedValue([]),
      getFacultyFacultyGet: vi.fn().mockResolvedValue([]),
      exportInvitesApiInvitesExportGet: vi.fn().mockResolvedValue(mockInviteRows),
    };
    vi.spyOn(generated, 'getAutomatedCourseSchedulerAPI').mockReturnValue(
      mockApi as unknown as ReturnType<typeof generated.getAutomatedCourseSchedulerAPI>,
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows the Export Invite CSV button for admin users', async () => {
    render(<Faculty />);
    await waitFor(() =>
      expect(screen.getByText('Export Invite CSV')).toBeInTheDocument(),
    );
  });

  it('calls the export endpoint when the button is clicked', async () => {
    const user = userEvent.setup();
    render(<Faculty />);
    await waitFor(() =>
      expect(screen.getByText('Export Invite CSV')).toBeInTheDocument(),
    );
    await user.click(screen.getByText('Export Invite CSV'));
    expect(mockApi.exportInvitesApiInvitesExportGet).toHaveBeenCalledOnce();
  });

  it('shows "Exporting…" while the request is in flight', async () => {
    let resolveExport!: (rows: InviteLinkResponse[]) => void;
    mockApi.exportInvitesApiInvitesExportGet = vi.fn().mockReturnValue(
      new Promise<InviteLinkResponse[]>((r) => { resolveExport = r; }),
    );

    const user = userEvent.setup();
    render(<Faculty />);
    await waitFor(() =>
      expect(screen.getByText('Export Invite CSV')).toBeInTheDocument(),
    );
    await user.click(screen.getByText('Export Invite CSV'));
    expect(screen.getByText('Exporting…')).toBeInTheDocument();
    resolveExport([]);
  });

  it('creates a blob and triggers a download after a successful export', async () => {
    const appendSpy = vi.spyOn(document.body, 'appendChild');

    const user = userEvent.setup();
    render(<Faculty />);
    await waitFor(() =>
      expect(screen.getByText('Export Invite CSV')).toBeInTheDocument(),
    );
    await user.click(screen.getByText('Export Invite CSV'));

    await waitFor(() =>
      expect(screen.getByText('Export Invite CSV')).toBeInTheDocument(),
    );

    // A blob URL was created from the CSV content
    expect(createObjectURLSpy).toHaveBeenCalledOnce();
    const [blob] = createObjectURLSpy.mock.calls[0] as [Blob];
    expect(blob).toBeInstanceOf(Blob);
    expect(blob.type).toBe('text/csv');

    // An anchor was appended with the correct download filename
    const anchor = appendSpy.mock.calls
      .map(([el]) => el as HTMLElement)
      .find((el) => el.tagName === 'A') as HTMLAnchorElement | undefined;
    expect(anchor?.download).toBe('faculty_invites.csv');
  });

  it('escapes double-quotes in CSV fields', async () => {
    const rowWithQuote: InviteLinkResponse[] = [
      {
        first_name: 'Ann "Annie"',
        last_name: 'Smith',
        email: 'ann@example.com',
        invite_link: 'https://example.com',
      },
    ];
    mockApi.exportInvitesApiInvitesExportGet = vi.fn().mockResolvedValue(rowWithQuote);

    const user = userEvent.setup();
    render(<Faculty />);
    await waitFor(() =>
      expect(screen.getByText('Export Invite CSV')).toBeInTheDocument(),
    );
    await user.click(screen.getByText('Export Invite CSV'));

    await waitFor(() => expect(createObjectURLSpy).toHaveBeenCalled());

    const [blob] = createObjectURLSpy.mock.calls[0] as [Blob];
    const csvContent = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = () => reject(reader.error);
      reader.readAsText(blob);
    });
    // Double-quotes inside a field must be escaped as ""
    expect(csvContent).toContain('"Ann ""Annie"""');
  });
});
