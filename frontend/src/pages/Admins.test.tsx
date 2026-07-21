import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import Admins from './Admins';
import * as generated from '../api/generated';
import type { UserResponse } from '../api/generated';

const mockAdmin: UserResponse = {
  user_id: 1,
  nuid: 9999,
  first_name: 'Admin',
  last_name: 'User',
  email: 'admin@example.com',
  role: 'ADMIN',
  active: true,
  has_signed_up: true,
};

vi.mock('../context/UserContext', () => ({
  useUser: () => ({ me: mockAdmin, meError: null, meLoading: false }),
}));

const mockUsers: UserResponse[] = [
  { user_id: 1, nuid: 100, first_name: 'Alice', last_name: 'Active', email: 'alice@example.com', role: 'ADMIN', active: true, has_signed_up: true },
  { user_id: 2, nuid: 200, first_name: 'Pat', last_name: 'Pending', email: 'pat@example.com', role: 'ADMIN', active: true, has_signed_up: false },
  { user_id: 3, nuid: 300, first_name: 'Ida', last_name: 'Inactive', email: 'ida@example.com', role: 'ADMIN', active: false, has_signed_up: true },
  { user_id: 4, nuid: 400, first_name: 'Vic', last_name: 'Viewer', email: 'vic@example.com', role: 'VIEWER', active: true, has_signed_up: true },
];

describe('Admins page', () => {
  let mockApi: Record<string, ReturnType<typeof vi.fn>>;

  beforeEach(() => {
    mockApi = {
      listUsersApiUsersGet: vi.fn().mockResolvedValue(mockUsers),
      createAdminInviteApiInvitesAdminPost: vi.fn(),
    };
    vi.spyOn(generated, 'getAutomatedCourseSchedulerAPI').mockReturnValue(
      mockApi as unknown as ReturnType<typeof generated.getAutomatedCourseSchedulerAPI>,
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('lists only ADMIN users, excluding viewers', async () => {
    render(<Admins />);
    await waitFor(() => expect(screen.getByText('Active, Alice')).toBeInTheDocument());
    expect(screen.getByText('Pending, Pat')).toBeInTheDocument();
    expect(screen.getByText('Inactive, Ida')).toBeInTheDocument();
    // VIEWER role must not appear
    expect(screen.queryByText('Viewer, Vic')).not.toBeInTheDocument();
  });

  it('renders the correct account-status badge per admin', async () => {
    render(<Admins />);
    await waitFor(() => expect(screen.getByText('Active, Alice')).toBeInTheDocument());
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Pending signup')).toBeInTheDocument();
    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });

  it('opens the invite-admin modal when the Invite admin button is clicked', async () => {
    const user = userEvent.setup();
    render(<Admins />);
    await waitFor(() => expect(screen.getByText('Active, Alice')).toBeInTheDocument());

    await user.click(screen.getByRole('button', { name: /invite admin/i }));

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Invite an administrator')).toBeInTheDocument();
  });

  it('creates an invite and shows the signup link', async () => {
    mockApi.createAdminInviteApiInvitesAdminPost.mockResolvedValue({
      user: { user_id: 5, nuid: 12345678, first_name: 'New', last_name: 'Admin', email: 'new@example.com', role: 'ADMIN', active: true, has_signed_up: false },
      signup_url: 'https://auth0.example/signup?login_hint=new@example.com',
    });
    const user = userEvent.setup();
    render(<Admins />);
    await waitFor(() => expect(screen.getByText('Active, Alice')).toBeInTheDocument());

    await user.click(screen.getByRole('button', { name: /invite admin/i }));
    await user.type(screen.getByPlaceholderText('e.g. 12345678'), '12345678');
    await user.type(screen.getByPlaceholderText('Jane'), 'New');
    await user.type(screen.getByPlaceholderText('Doe'), 'Admin');
    await user.type(screen.getByPlaceholderText('j.doe@northeastern.edu'), 'new@example.com');
    await user.click(screen.getByRole('button', { name: /generate invite link/i }));

    await waitFor(() =>
      expect(screen.getByDisplayValue('https://auth0.example/signup?login_hint=new@example.com')).toBeInTheDocument(),
    );
    expect(mockApi.createAdminInviteApiInvitesAdminPost).toHaveBeenCalledWith({
      nuid: 12345678,
      first_name: 'New',
      last_name: 'Admin',
      email: 'new@example.com',
    });
    // Newly-invited admin appears in the list
    expect(screen.getByText('Admin, New')).toBeInTheDocument();
  });
});
