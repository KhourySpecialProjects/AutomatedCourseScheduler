import { useEffect, useMemo, useState } from 'react';
import { useUser } from '../context/UserContext';
import {
  getAutomatedCourseSchedulerAPI,
  type InviteResponse,
  type UserResponse,
} from '../api/generated';

// ── Account status helpers ──────────────────────────────────────────────────

type AccountStatus = 'active' | 'pending' | 'inactive';

function accountStatus(user: UserResponse): AccountStatus {
  if (!user.active) return 'inactive';
  return user.has_signed_up ? 'active' : 'pending';
}

function StatusBadge({ status }: { status: AccountStatus }) {
  const styles: Record<AccountStatus, string> = {
    active: 'bg-green-100 text-green-800',
    pending: 'bg-amber-100 text-amber-800',
    inactive: 'bg-gray-100 text-gray-500',
  };
  const labels: Record<AccountStatus, string> = {
    active: 'Active',
    pending: 'Pending signup',
    inactive: 'Inactive',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

// Narrow an unknown axios error to its API `detail` message without unchecked casts.
function extractApiErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = err.response;
    if (response && typeof response === 'object' && 'data' in response) {
      const data = response.data;
      if (data && typeof data === 'object' && 'detail' in data) {
        const detail = data.detail;
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) {
          const msg = detail
            .map((e) => (e && typeof e === 'object' && 'msg' in e && typeof e.msg === 'string' ? e.msg : ''))
            .filter(Boolean)
            .join(' ');
          if (msg) return msg;
        }
      }
    }
  }
  return fallback;
}

// ── Main component ──────────────────────────────────────────────────────────

export default function Admins() {
  const { me, meLoading } = useUser();

  const [admins, setAdmins] = useState<UserResponse[]>([]);
  const [loading, setLoading] = useState(true);

  // Invite-admin modal state
  const [inviteOpen, setInviteOpen] = useState(false);
  const [formNuid, setFormNuid] = useState('');
  const [formFirstName, setFormFirstName] = useState('');
  const [formLastName, setFormLastName] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [inviting, setInviting] = useState(false);
  const [inviteResult, setInviteResult] = useState<InviteResponse | null>(null);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteCopied, setInviteCopied] = useState(false);

  const api = getAutomatedCourseSchedulerAPI();

  useEffect(() => {
    setLoading(true);
    getAutomatedCourseSchedulerAPI()
      .listUsersApiUsersGet()
      .then((users) => setAdmins(users.filter((u) => u.role === 'ADMIN')))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const displayedAdmins = useMemo(
    () =>
      [...admins].sort((a, b) => {
        const an = `${a.last_name} ${a.first_name}`.toLowerCase();
        const bn = `${b.last_name} ${b.first_name}`.toLowerCase();
        return an.localeCompare(bn);
      }),
    [admins],
  );

  function openInviteModal() {
    setInviteResult(null);
    setInviteError(null);
    setInviteCopied(false);
    setFormNuid('');
    setFormFirstName('');
    setFormLastName('');
    setFormEmail('');
    setInviteOpen(true);
  }

  function closeInviteModal() {
    setInviteOpen(false);
    setInviteResult(null);
    setInviteError(null);
    setInviteCopied(false);
    setFormNuid('');
    setFormFirstName('');
    setFormLastName('');
    setFormEmail('');
  }

  async function handleGenerateInvite() {
    const nuid = Number.parseInt(formNuid.trim(), 10);
    if (!Number.isFinite(nuid) || nuid < 1) {
      setInviteError('Enter a valid NUID (positive number).');
      return;
    }
    const first = formFirstName.trim();
    const last = formLastName.trim();
    const email = formEmail.trim();
    if (!first || !last || !email) {
      setInviteError('First name, last name, and email are required.');
      return;
    }
    setInviting(true);
    setInviteError(null);
    try {
      const result = await api.createAdminInviteApiInvitesAdminPost({
        nuid,
        first_name: first,
        last_name: last,
        email,
      });
      setInviteResult(result);
      // Reflect the newly-invited admin in the list immediately.
      setAdmins((prev) =>
        prev.some((u) => u.nuid === result.user.nuid) ? prev : [...prev, result.user],
      );
    } catch (err: unknown) {
      setInviteError(extractApiErrorMessage(err, 'Failed to create invite. Please try again.'));
    } finally {
      setInviting(false);
    }
  }

  function copyInviteUrl(url: string) {
    navigator.clipboard.writeText(url).then(() => {
      setInviteCopied(true);
      setTimeout(() => setInviteCopied(false), 2000);
    });
  }

  // ── Guard: still resolving identity ──
  if (meLoading) {
    return (
      <div className="flex items-center gap-2 text-gray-400 text-sm">
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        Loading…
      </div>
    );
  }

  // ── Guard: admin only ──
  if (me?.role !== 'ADMIN') {
    return (
      <div className="max-w-md mt-8">
        <div className="p-6 bg-red-50 border border-red-200 rounded-xl">
          <h2 className="text-base font-semibold text-red-800 mb-1">Admin access required</h2>
          <p className="text-sm text-red-700">
            This page is only available to administrators. Contact your admin if you need access.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl space-y-6">
      {/* Page header */}
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Administrators</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage who has administrator access and invite new administrators.
          </p>
        </div>
        <button
          type="button"
          onClick={openInviteModal}
          title="Create a pending admin account and copy an Auth0 signup link (no faculty record required)"
          className="shrink-0 flex items-center gap-1.5 px-3 py-2 text-sm font-medium bg-burgundy-600 text-white rounded-lg hover:bg-burgundy-700 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
          Invite admin
        </button>
      </div>

      {/* Admins list card */}
      <div className="bg-white border border-gray-200 rounded-xl">
        {loading ? (
          <div className="px-5 py-8 text-sm text-gray-400">Loading administrators…</div>
        ) : displayedAdmins.length === 0 ? (
          <div className="px-5 py-8 text-sm text-gray-400 text-center">No administrators found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-100">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Account</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {displayedAdmins.map((a) => {
                  const status = accountStatus(a);
                  return (
                    <tr key={a.user_id} className={status === 'inactive' ? 'opacity-50' : ''}>
                      <td className="px-5 py-3">
                        <div className="text-sm font-medium text-gray-900">
                          {a.last_name}, {a.first_name}
                        </div>
                        <div className="text-xs text-gray-400">{a.nuid}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">{a.email}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={status} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {!loading && (
          <div className="px-5 py-3 border-t border-gray-100 text-xs text-gray-400">
            {displayedAdmins.length} administrator{displayedAdmins.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {inviteOpen && (
        <>
          <div className="fixed inset-0 bg-black/20 z-40" onClick={closeInviteModal} aria-hidden />
          <div
            role="dialog"
            aria-labelledby="invite-admin-title"
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg max-h-[90vh] overflow-y-auto bg-white rounded-xl shadow-xl border border-gray-100 p-6"
          >
            <h2 id="invite-admin-title" className="text-base font-semibold text-gray-900 mb-1">
              Invite an administrator
            </h2>
            <p className="text-sm text-gray-500 mb-4">
              Creates a pending admin user in the database (no faculty row). The person must sign up in Auth0 using{' '}
              <span className="font-medium">this exact email</span> so their account links and they get admin access.
            </p>
            {!inviteResult?.signup_url && (
              <div className="space-y-3 mb-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    NUID
                  </label>
                  <input
                    type="text"
                    inputMode="numeric"
                    autoComplete="off"
                    value={formNuid}
                    onChange={(e) => setFormNuid(e.target.value.replace(/\D/g, ''))}
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-burgundy-500"
                    placeholder="e.g. 12345678"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                      First name
                    </label>
                    <input
                      type="text"
                      value={formFirstName}
                      onChange={(e) => setFormFirstName(e.target.value)}
                      className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-burgundy-500"
                      placeholder="Jane"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                      Last name
                    </label>
                    <input
                      type="text"
                      value={formLastName}
                      onChange={(e) => setFormLastName(e.target.value)}
                      className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-burgundy-500"
                      placeholder="Doe"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    Email
                  </label>
                  <input
                    type="email"
                    autoComplete="email"
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-burgundy-500"
                    placeholder="j.doe@northeastern.edu"
                  />
                </div>
              </div>
            )}
            {inviteError && (
              <div className="mb-3 p-2.5 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {inviteError}
              </div>
            )}
            {inviteResult?.signup_url ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <p className="text-xs text-gray-500">Share this signup link:</p>
                  <div className="flex items-center gap-2">
                    <input
                      readOnly
                      value={inviteResult.signup_url}
                      className="flex-1 text-xs border border-gray-200 rounded-lg px-3 py-2 bg-gray-50 text-gray-700 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => copyInviteUrl(inviteResult.signup_url)}
                      className="shrink-0 px-3 py-2 text-xs font-medium bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      {inviteCopied ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                </div>
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={closeInviteModal}
                    className="px-4 py-2 text-sm font-medium bg-burgundy-600 text-white rounded-lg hover:bg-burgundy-700 transition-colors"
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={closeInviteModal}
                  className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => void handleGenerateInvite()}
                  disabled={inviting}
                  className="px-4 py-2 text-sm font-medium bg-burgundy-600 text-white rounded-lg hover:bg-burgundy-700 disabled:opacity-50 transition-colors"
                >
                  {inviting ? 'Generating…' : 'Generate invite link'}
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
