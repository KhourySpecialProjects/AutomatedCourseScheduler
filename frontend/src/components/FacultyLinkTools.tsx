import { useEffect, useState } from 'react';
import { getAutomatedCourseSchedulerAPI, type FacultyResponse } from '../api/generated';
import SearchableSelect, { type SelectOption } from './SearchableSelect';

export default function FacultyLinkTools({
  disabled,
  onGenerate,
}: {
  disabled: boolean;
  onGenerate: (facultyNuid: number | null) => void;
}) {
  const [facultyOptions, setFacultyOptions] = useState<SelectOption<number>[]>([]);
  const [selectedFacultyNuid, setSelectedFacultyNuid] = useState<number | null>(null);

  useEffect(() => {
    getAutomatedCourseSchedulerAPI()
      .getFacultyFacultyGet({ active_only: true })
      .then((faculty: FacultyResponse[]) => {
        setFacultyOptions(
          faculty.map((f) => ({
            value: f.NUID,
            label: `${f.FirstName ?? ''} ${f.LastName ?? ''}`.trim() || `Faculty ${f.NUID}`,
            sublabel: [f.Email, `NUID ${f.NUID}`].filter(Boolean).join(' · '),
          })),
        );
      })
      .catch(() => {});
  }, []);

  return (
    <div className="flex items-center gap-2">
      <div className="w-64">
        <SearchableSelect
          options={facultyOptions}
          value={selectedFacultyNuid}
          onChange={setSelectedFacultyNuid}
          placeholder="Select faculty…"
          disabled={disabled}
        />
      </div>
      <button
        onClick={() => onGenerate(selectedFacultyNuid)}
        disabled={disabled}
        className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-60 transition-colors"
        title="Generate faculty invite link (TODO)"
      >
        Generate faculty link
      </button>
    </div>
  );
}

