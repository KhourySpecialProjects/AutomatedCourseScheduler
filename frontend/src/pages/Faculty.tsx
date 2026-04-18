import { useEffect, useMemo, useState } from 'react';
import {
  getAutomatedCourseSchedulerAPI,
  type CampusResponse,
  type ScheduleResponse,
  type SectionRichResponse,
  type UserResponse,
} from '../api/generated';
import FacultyDrawer, { type FacultyRecord } from '../components/FacultyDrawer';
import SearchableSelect, { type SelectOption } from '../components/SearchableSelect';

// ── Histogram helpers ──────────────────────────────────────────────────────

type BucketKey = 'first' | 'second' | 'third' | 'none';

function bucketLabel(k: BucketKey) {
  switch (k) {
    case 'first': return '1st choice';
    case 'second': return '2nd choice';
    case 'third': return '3rd choice';
    case 'none': return 'Not Assigned Preference';
  }
}

function bucketStyle(k: BucketKey) {
  switch (k) {
    case 'first': return 'bg-green-600';
    case 'second': return 'bg-amber-500';
    case 'third': return 'bg-red-500';
    case 'none': return 'bg-red-800';
  }
}

function preferenceToBucket(pref?: string): BucketKey {
  if (pref === 'Eager to teach') return 'first';
  if (pref === 'Willing to teach') return 'second';
  if (pref === 'Not my cup of tea') return 'third';
  return 'none';
}

function Bar({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="text-gray-500">{value} ({pct}%)</span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ── Sort helpers ───────────────────────────────────────────────────────────

type SortKey = 'name' | 'load';
type SortDir = 'asc' | 'desc';

// ── Main component ─────────────────────────────────────────────────────────

export default function Faculty() {
  // Auth
  const [me, setMe] = useState<UserResponse | null>(null);
  const [meLoading, setMeLoading] = useState(true);

  // Schedule / sections (shared with histogram)
  const [schedules, setSchedules] = useState<ScheduleResponse[]>([]);
  const [selectedScheduleId, setSelectedScheduleId] = useState<number | null>(null);
  const [sections, setSections] = useState<SectionRichResponse[]>([]);
  const [sectionsLoading, setSectionsLoading] = useState(false);

  // Campuses
  const [campuses, setCampuses] = useState<CampusResponse[]>([]);

  // Faculty list
  const [facultyList, setFacultyList] = useState<FacultyRecord[]>([]);
  const [facultyLoading, setFacultyLoading] = useState(true);

  // Users with accounts (for invite status)
  const [userNuidSet, setUserNuidSet] = useState<Set<number>>(new Set());

  // Filters & sort
  const [nameSearch, setNameSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  // Drawer state
  type DrawerState =
    | { mode: 'create' }
    | { mode: 'edit'; faculty: FacultyRecord }
    | null;
  const [drawer, setDrawer] = useState<DrawerState>(null);

  // Export state
  const [exporting, setExporting] = useState(false);

  const api = getAutomatedCourseSchedulerAPI();

  // Fetch current user
  useEffect(() => {
    api
      .getMeApiUsersMeGet()
      .then(setMe)
      .catch(() => {})
      .finally(() => setMeLoading(false));
  }, []);

  // Fetch campuses + schedules + users on mount
  useEffect(() => {
    api.getAllCampusesCampusesGet().then(setCampuses).catch(() => {});
    api
      .getSchedulesSchedulesGet()
      .then((data) => {
        setSchedules(data);
        if (data.length > 0) setSelectedScheduleId((prev) => prev ?? data[0].schedule_id);
      })
      .catch(() => {});
    api
      .listUsersApiUsersGet()
      .then((users) => setUserNuidSet(new Set(users.map((u) => u.nuid))))
      .catch(() => {});
  }, []);

  // Fetch faculty list once on mount
  useEffect(() => {
    setFacultyLoading(true);
    (api.getFacultyFacultyGet({}) as unknown as Promise<FacultyRecord[]>)
      .then(setFacultyList)
      .catch(() => {})
      .finally(() => setFacultyLoading(false));
  }, []);

  // Fetch sections when schedule changes
  useEffect(() => {
    if (!selectedScheduleId) {
      setSections([]);
      return;
    }
    let cancelled = false;
    setSectionsLoading(true);
    api
      .getScheduleSectionsRichSchedulesScheduleIdSectionsRichGet(selectedScheduleId)
      .then((secs) => {
        if (!cancelled) setSections(secs);
      })
      .catch(() => {
        if (!cancelled) setSections([]);
      })
      .finally(() => {
        if (!cancelled) setSectionsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedScheduleId]);

  // Current load per faculty in selected schedule
  const loadMap = useMemo(() => {
    const map = new Map<number, number>();
    for (const s of sections) {
      for (const inst of s.instructors) {
        map.set(inst.nuid, (map.get(inst.nuid) ?? 0) + 1);
      }
    }
    return map;
  }, [sections]);

  // Histogram counts
  const counts = useMemo(() => {
    const c: Record<BucketKey, number> = { first: 0, second: 0, third: 0, none: 0 };
    for (const s of sections) {
      for (const inst of s.instructors) {
        const pref = inst.course_preferences.find((cp) => cp.course_id === s.course.course_id)?.preference;
        c[preferenceToBucket(pref)] += 1;
      }
    }
    return c;
  }, [sections]);
  const totalAssignments = counts.first + counts.second + counts.third + counts.none;

  // Time preference histogram counts
  const timeCounts = useMemo(() => {
    const c: Record<BucketKey, number> = { first: 0, second: 0, third: 0, none: 0 };
    for (const s of sections) {
      for (const inst of s.instructors) {
        const pref = inst.meeting_preferences.find(
          (mp) => mp.time_block_id === s.time_block.time_block_id,
        )?.preference;
        c[preferenceToBucket(pref)] += 1;
      }
    }
    return c;
  }, [sections]);
  const totalTimeAssignments = timeCounts.first + timeCounts.second + timeCounts.third + timeCounts.none;

  // Schedule dropdown options
  const scheduleOptions: SelectOption<number>[] = useMemo(
    () =>
      schedules.map((s) => ({
        value: s.schedule_id,
        label: s.name,
        sublabel: `Semester ${s.semester_id}`,
      })),
    [schedules],
  );

  // Campus name lookup
  const campusNameMap = useMemo(
    () => new Map(campuses.map((c) => [c.campus_id, c.name])),
    [campuses],
  );

  // Filtered + sorted faculty list
  const displayedFaculty = useMemo(() => {
    const q = nameSearch.trim().toLowerCase();
    let list = facultyList.filter((f) => {
      if (q) {
        const full = `${f.first_name ?? ''} ${f.last_name ?? ''}`.toLowerCase();
        if (!full.includes(q)) return false;
      }
      return true;
    });

    list = [...list].sort((a, b) => {
      let cmp = 0;
      if (sortKey === 'name') {
        const an = `${a.last_name ?? ''} ${a.first_name ?? ''}`.toLowerCase();
        const bn = `${b.last_name ?? ''} ${b.first_name ?? ''}`.toLowerCase();
        cmp = an.localeCompare(bn);
      } else {
        const al = loadMap.get(a.nuid) ?? 0;
        const bl = loadMap.get(b.nuid) ?? 0;
        cmp = al - bl;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return list;
  }, [facultyList, nameSearch, sortKey, sortDir, loadMap]);

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('asc'); }
  }

  async function handleExportInviteCsv() {
    setExporting(true);
    try {
      const rows = await api.exportInvitesApiInvitesExportGet();
      const header = ['first_name', 'last_name', 'email', 'invite_link'];
      const escape = (v: string) => `"${v.replace(/"/g, '""')}"`;
      const csv = [
        header.join(','),
        ...rows.map((r) => [r.first_name, r.last_name, r.email, r.invite_link].map(escape).join(',')),
      ].join('\n');
      const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'faculty_invites.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      const users = await api.listUsersApiUsersGet();
      setUserNuidSet(new Set(users.map((u) => u.nuid)));
    } finally {
      setExporting(false);
    }
  }

  function handleSaved(updated: FacultyRecord) {
    setFacultyList((prev) => {
      const idx = prev.findIndex((f) => f.nuid === updated.nuid);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = updated;
        return next;
      }
      return [updated, ...prev];
    });
    setDrawer(null);
  }

  function handleDeleted(nuid: number) {
    setFacultyList((prev) => prev.filter((f) => f.nuid !== nuid));
    setDrawer(null);
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
    <div className="max-w-5xl space-y-6">
      {/* Page header */}
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Faculty</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage faculty members and view preference satisfaction by schedule.
          </p>
        </div>
        <div className="w-72 mt-1 shrink-0">
          <SearchableSelect
            options={scheduleOptions}
            value={selectedScheduleId}
            onChange={setSelectedScheduleId}
            placeholder="Select schedule…"
            disabled={schedules.length === 0}
          />
        </div>
      </div>

      {/* ── Histogram card ── */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="mb-5">
          <div className="text-sm font-semibold text-gray-900">Assignment Preferences</div>
          <div className="text-xs text-gray-500">
            Instructor-to-section assignments by preference bucket.
          </div>
        </div>

        {sectionsLoading ? (
          <div className="text-sm text-gray-400">Loading…</div>
        ) : (
          <div className="grid grid-cols-2 gap-8">
            <div>
              <div className="text-xs font-medium text-gray-600 mb-3">Course</div>
              <div className="space-y-4">
                <Bar label={bucketLabel('first')} value={counts.first} total={totalAssignments} color={bucketStyle('first')} />
                <Bar label={bucketLabel('second')} value={counts.second} total={totalAssignments} color={bucketStyle('second')} />
                <Bar label={bucketLabel('third')} value={counts.third} total={totalAssignments} color={bucketStyle('third')} />
                <Bar label={bucketLabel('none')} value={counts.none} total={totalAssignments} color={bucketStyle('none')} />
              </div>
            </div>
            <div>
              <div className="text-xs font-medium text-gray-600 mb-3">Time</div>
              <div className="space-y-4">
                <Bar label={bucketLabel('first')} value={timeCounts.first} total={totalTimeAssignments} color={bucketStyle('first')} />
                <Bar label={bucketLabel('second')} value={timeCounts.second} total={totalTimeAssignments} color={bucketStyle('second')} />
                <Bar label={bucketLabel('third')} value={timeCounts.third} total={totalTimeAssignments} color={bucketStyle('third')} />
                <Bar label={bucketLabel('none')} value={timeCounts.none} total={totalTimeAssignments} color={bucketStyle('none')} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Faculty list card ── */}
      <div className="bg-white border border-gray-200 rounded-xl">
        {/* Card header */}
        <div className="flex flex-wrap items-center gap-3 px-5 py-4 border-b border-gray-100">
          <div className="text-sm font-semibold text-gray-900 mr-auto">All Faculty</div>

          {/* Name search */}
          <div className="relative">
            <svg
              className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" />
            </svg>
            <input
              type="text"
              value={nameSearch}
              onChange={(e) => setNameSearch(e.target.value)}
              placeholder="Search name…"
              className="pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-burgundy-500 w-44"
            />
          </div>

          {/* Export invite CSV */}
          <button
            onClick={handleExportInviteCsv}
            disabled={exporting}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {exporting ? 'Exporting…' : 'Export Invite CSV'}
          </button>

          {/* Add faculty */}
          <button
            onClick={() => setDrawer({ mode: 'create' })}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-burgundy-600 text-white rounded-lg hover:bg-burgundy-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Faculty
          </button>
        </div>

        {/* Table */}
        {facultyLoading ? (
          <div className="px-5 py-8 text-sm text-gray-400">Loading faculty…</div>
        ) : displayedFaculty.length === 0 ? (
          <div className="px-5 py-8 text-sm text-gray-400 text-center">No faculty found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-100">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    onClick={() => handleSort('name')}
                    className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:bg-gray-100 transition-colors"
                  >
                    <span className="flex items-center gap-1">
                      Name
                      {sortKey === 'name' ? (
                        <svg className="w-3 h-3 text-burgundy-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sortDir === 'asc' ? 'M5 15l7-7 7 7' : 'M19 9l-7 7-7-7'} />
                        </svg>
                      ) : (
                        <svg className="w-3 h-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4" />
                        </svg>
                      )}
                    </span>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Campus</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Max Load</th>
                  <th
                    onClick={() => handleSort('load')}
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:bg-gray-100 transition-colors"
                  >
                    <span className="flex items-center gap-1">
                      Current Load
                      {sortKey === 'load' ? (
                        <svg className="w-3 h-3 text-burgundy-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sortDir === 'asc' ? 'M5 15l7-7 7 7' : 'M19 9l-7 7-7-7'} />
                        </svg>
                      ) : (
                        <svg className="w-3 h-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4" />
                        </svg>
                      )}
                      {!selectedScheduleId && (
                        <span className="ml-1 text-gray-300 normal-case font-normal">(no schedule)</span>
                      )}
                    </span>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Account</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {displayedFaculty.map((f) => {
                  const currentLoad = loadMap.get(f.nuid) ?? 0;
                  const overloaded = selectedScheduleId !== null && currentLoad > (f.maxLoad ?? 3);
                  const inactive = !f.active;

                  return (
                    <tr
                      key={f.nuid}
                      onClick={() => setDrawer({ mode: 'edit', faculty: f })}
                      className={`cursor-pointer transition-colors hover:bg-burgundy-50/40 ${inactive ? 'opacity-50' : ''}`}
                    >
                      {/* Name */}
                      <td className="px-5 py-3">
                        <div className={`text-sm font-medium text-gray-900 ${inactive ? 'italic' : ''}`}>
                          {f.last_name}, {f.first_name}
                        </div>
                        <div className="text-xs text-gray-400">{f.nuid}</div>
                      </td>

                      {/* Campus */}
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {f.campus !== null
                          ? (campusNameMap.get(f.campus) ?? `#${f.campus}`)
                          : <span className="text-gray-300">—</span>}
                      </td>

                      {/* Max Load */}
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {f.maxLoad ?? 3}
                      </td>

                      {/* Current Load */}
                      <td className="px-4 py-3">
                        {selectedScheduleId !== null ? (
                          <span
                            className={`text-sm font-medium ${
                              overloaded
                                ? 'text-red-600'
                                : currentLoad === 0
                                  ? 'text-amber-600'
                                  : 'text-gray-700'
                            }`}
                            title={
                              overloaded
                                ? 'Exceeds max load'
                                : currentLoad === 0
                                  ? 'No load assigned'
                                  : undefined
                            }
                          >
                            {currentLoad}
                            {overloaded && (
                              <span className="ml-1 text-xs text-red-500">⚠</span>
                            )}
                            {currentLoad === 0 && (
                              <span className="ml-1 text-xs text-amber-500">⚠</span>
                            )}
                          </span>
                        ) : (
                          <span className="text-sm text-gray-300">—</span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            f.active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-500'
                          }`}
                        >
                          {f.active ? 'Active' : 'Inactive'}
                        </span>
                      </td>

                      {/* Account */}
                      <td className="px-4 py-3">
                        {userNuidSet.has(f.nuid) ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-burgundy-50 text-burgundy-700">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Linked
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">No account</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Row count */}
        {!facultyLoading && (
          <div className="px-5 py-3 border-t border-gray-100 text-xs text-gray-400">
            {displayedFaculty.length} of {facultyList.length} faculty member{facultyList.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Drawer */}
      {drawer && (
        <FacultyDrawer
          mode={drawer.mode}
          faculty={drawer.mode === 'edit' ? drawer.faculty : null}
          sections={sections}
          campuses={campuses}
          scheduleId={selectedScheduleId}
          hasAccount={drawer.mode === 'edit' ? userNuidSet.has(drawer.faculty.nuid) : false}
          onClose={() => setDrawer(null)}
          onSaved={handleSaved}
          onDeleted={handleDeleted}
          onInvited={(nuid) => setUserNuidSet((prev) => new Set([...prev, nuid]))}
        />
      )}
    </div>
  );
}
