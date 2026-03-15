import type { SectionResponse } from '../api/generated';

interface SectionsTableProps {
  sections: SectionResponse[];
}

function SectionsTable({ sections }: SectionsTableProps) {
  if (sections.length === 0) {
    return <p className="text-gray-500 mt-4">No sections found.</p>;
  }

  return (
    <div className="mt-4 overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
        <thead className="bg-gray-50">
          <tr>
            {['Section ID', 'Schedule', 'Time Block', 'Course', 'Capacity', 'Instructor'].map(
              (header) => (
                <th
                  key={header}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {header}
                </th>
              ),
            )}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sections.map((section) => (
            <tr key={section.SectionID} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {section.SectionID}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {section.Schedule ?? '—'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {section.TimeBlock ?? '—'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {section.Course ?? '—'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {section.Capacity ?? '—'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {section.Instructor ?? '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default SectionsTable;
