import SectionsTable from '../components/SectionsTable';
import { useSections } from '../hooks/useSections';

function Sections() {
  const { sections, loading, error } = useSections();

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900">Sections</h1>
      {loading && <p className="mt-4 text-gray-500">Loading...</p>}
      {error && <p className="mt-4 text-red-600">{error}</p>}
      {!loading && !error && <SectionsTable sections={sections} />}
    </div>
  );
}

export default Sections;
